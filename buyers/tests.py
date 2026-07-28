import pytest
from buyers.factories import BuyerFactory, BuyerCarPreferenceFactory

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
        from dealerships.factories import UserFactory
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
        from cars.factories import CarFactory
        c = CarFactory()
        data = {'buyer': buyer_user.pk, 'car': c.pk, 'max_price': '25000.00'}
        resp = buyer_auth_client.post(PREF_URL, data, format='json')
        assert resp.status_code == 201
