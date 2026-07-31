import pytest
from decimal import Decimal
from moneyed import Money
from buyers.factories import BuyerFactory, BuyerCarPreferenceFactory
from dealerships.factories import DealershipFactory, DealershipInventoryFactory, UserFactory
from cars.factories import CarFactory
from offers.models import Offer, OfferStatus

BUYER_URL = '/api/v1/buyers/'
PREF_URL = '/api/v1/buyer-preferences/'
STATS_URL = '/api/v1/buyers/{}/statistics/'


def _url(base, pk):
    return f'{base}{pk}/'


@pytest.mark.django_db
class TestBuyerAPI:
    def test_list_admin_only(self, auth_client, buyer_auth_client):
        BuyerFactory.create_batch(2)
        assert auth_client.get(BUYER_URL).status_code == 200
        assert buyer_auth_client.get(BUYER_URL).status_code == 403

    def test_retrieve(self, auth_client):
        b = BuyerFactory()
        resp = auth_client.get(_url(BUYER_URL, b.pk))
        assert resp.status_code == 200

    def test_create(self, auth_client):
        u = UserFactory()
        data = {'user': u.pk, 'balance': '50000.00'}
        resp = auth_client.post(BUYER_URL, data, format='json')
        assert resp.status_code == 201

    def test_statistics(self, auth_client):
        b = BuyerFactory()
        resp = auth_client.get(STATS_URL.format(b.pk))
        assert resp.status_code == 200
        assert resp.data['total_spent'] == '0.00'

    def test_statistics_own(self, buyer_auth_client, buyer_user):
        resp = buyer_auth_client.get(STATS_URL.format(buyer_user.pk))
        assert resp.status_code == 200

    def test_statistics_other_denied(self, buyer_auth_client):
        other = BuyerFactory()
        resp = buyer_auth_client.get(STATS_URL.format(other.pk))
        assert resp.status_code == 403


@pytest.mark.django_db
class TestBuyerPreferenceAPI:
    def test_list_own(self, buyer_auth_client, buyer_user):
        BuyerCarPreferenceFactory.create(buyer=buyer_user)
        resp = buyer_auth_client.get(PREF_URL)
        assert resp.status_code == 200
        assert len(resp.data['results']) == 1

    def test_create(self, buyer_auth_client, buyer_user):
        c = CarFactory()
        data = {'buyer': buyer_user.pk, 'car': c.pk, 'max_price': '25000.00'}
        resp = buyer_auth_client.post(PREF_URL, data, format='json')
        assert resp.status_code == 201


@pytest.mark.django_db
class TestBuyerOfferService:
    def test_accepts_matching_offer(self):
        from buyers.services import BuyerOfferService
        buyer = BuyerFactory(balance=Money(100_000, 'USD'))
        dealership = DealershipFactory(balance=Money(400_000, 'USD'))
        car = CarFactory()
        DealershipInventoryFactory(
            dealership=dealership, car=car, quantity=10,
            price_per_unit=Money(20_000, 'USD'),
        )
        offer = Offer.objects.create(
            buyer=buyer, car=car, quantity=2,
            max_budget=Money(25_000, 'USD'), status=OfferStatus.PENDING,
        )

        BuyerOfferService().run_for_buyer(buyer.pk)

        offer.refresh_from_db()
        assert offer.status == OfferStatus.ACCEPTED
        assert offer.dealership == dealership
        assert offer.offered_price is not None

        buyer.refresh_from_db()
        assert buyer.balance.amount < Decimal('100000.00')

    def test_rejects_offer_no_inventory_match(self):
        from buyers.services import BuyerOfferService
        buyer = BuyerFactory(balance=Money(100_000, 'USD'))
        car = CarFactory()
        offer = Offer.objects.create(
            buyer=buyer, car=car, quantity=1,
            max_budget=Money(30_000, 'USD'), status=OfferStatus.PENDING,
        )

        BuyerOfferService().run_for_buyer(buyer.pk)

        offer.refresh_from_db()
        assert offer.status == OfferStatus.REJECTED
        assert 'no dealership found' in offer.reason

    def test_skips_if_buyer_not_found(self):
        from buyers.services import BuyerOfferService
        svc = BuyerOfferService()
        svc.run_for_buyer(99999)

    def test_skips_if_unverified_email(self):
        from buyers.services import BuyerOfferService
        user = UserFactory(is_active=False)
        buyer = BuyerFactory(user=user)
        dealership = DealershipFactory()
        car = CarFactory()
        DealershipInventoryFactory(dealership=dealership, car=car, quantity=5, price_per_unit=Money(20_000, 'USD'))
        Offer.objects.create(
            buyer=buyer, car=car, quantity=1,
            max_budget=Money(30_000, 'USD'), status=OfferStatus.PENDING,
        )

        BuyerOfferService().run_for_buyer(buyer.pk)

        offer = Offer.objects.filter(buyer=buyer, status=OfferStatus.PENDING).first()
        assert offer is not None

    def test_skips_if_no_balance(self):
        from buyers.services import BuyerOfferService
        buyer = BuyerFactory(balance=Money(0, 'USD'))
        dealership = DealershipFactory()
        car = CarFactory()
        DealershipInventoryFactory(dealership=dealership, car=car, quantity=5, price_per_unit=Money(1000, 'USD'))
        Offer.objects.create(
            buyer=buyer, car=car, quantity=1,
            max_budget=Money(30_000, 'USD'), status=OfferStatus.PENDING,
        )

        BuyerOfferService().run_for_buyer(buyer.pk)

        offer = Offer.objects.get(buyer=buyer)
        assert offer.status == OfferStatus.PENDING

    def test_pref_cap_limits_max_price(self):
        from buyers.services import BuyerOfferService
        buyer = BuyerFactory(balance=Money(100_000, 'USD'))
        dealership = DealershipFactory(balance=Money(400_000, 'USD'))
        car = CarFactory()
        DealershipInventoryFactory(
            dealership=dealership, car=car, quantity=10,
            price_per_unit=Money(20_000, 'USD'),
        )
        BuyerCarPreferenceFactory(buyer=buyer, car=car, max_price=Money(15_000, 'USD'))

        offer = Offer.objects.create(
            buyer=buyer, car=car, quantity=1,
            max_budget=Money(30_000, 'USD'), status=OfferStatus.PENDING,
        )

        BuyerOfferService().run_for_buyer(buyer.pk)

        offer.refresh_from_db()
        assert offer.status == OfferStatus.REJECTED


@pytest.mark.django_db
class TestBuyerOfferViaCeleryTask:
    def test_process_buyer_offers_full_flow(self):
        from buyers.tasks import process_buyer_offers
        buyer = BuyerFactory(balance=Money(100_000, 'USD'))
        dealership = DealershipFactory(balance=Money(400_000, 'USD'))
        car = CarFactory()
        DealershipInventoryFactory(
            dealership=dealership, car=car, quantity=5,
            price_per_unit=Money(20_000, 'USD'),
        )
        Offer.objects.create(
            buyer=buyer, car=car, quantity=2,
            max_budget=Money(25000, 'USD'), status=OfferStatus.PENDING,
        )

        process_buyer_offers(buyer.pk)

        offer = Offer.objects.get(buyer=buyer)
        assert offer.status == OfferStatus.ACCEPTED
