import pytest
from dealerships.factories import (
    DealershipBestSupplierFactory,
    DealershipCarPreferenceFactory,
    DealershipFactory,
    DealershipInventoryFactory,
    PurchaseLogFactory,
    SaleRecordFactory,
)

DEALER_URL = '/api/v1/dealerships/'
INV_URL = '/api/v1/dealership-inventory/'
PREF_URL = '/api/v1/dealership-preferences/'
SALE_URL = '/api/v1/sale-records/'
PURCH_URL = '/api/v1/purchase-logs/'
BEST_URL = '/api/v1/best-suppliers/'
STATS_URL = '/api/v1/dealerships/{}/statistics/'


def _url(base, pk):
    return f'{base}{pk}/'


@pytest.mark.django_db
class TestDealershipAPI:
    def test_list(self, auth_client):
        DealershipFactory.create_batch(2)
        resp = auth_client.get(DEALER_URL)
        assert resp.status_code == 200
        assert len(resp.data['results']) == 2

    def test_create_admin_only(self, auth_client, buyer_auth_client):
        data = {'name': 'New', 'location': 'US', 'balance': '50000.00'}
        assert auth_client.post(DEALER_URL, data, format='json').status_code == 201
        assert buyer_auth_client.post(DEALER_URL, data, format='json').status_code == 403

    def test_retrieve(self, auth_client):
        d = DealershipFactory()
        resp = auth_client.get(_url(DEALER_URL, d.pk))
        assert resp.status_code == 200
        assert resp.data['name'] == d.name

    def test_soft_delete(self, auth_client):
        d = DealershipFactory()
        resp = auth_client.delete(_url(DEALER_URL, d.pk))
        assert resp.status_code == 204
        d.refresh_from_db()
        assert d.is_deleted is True

    def test_statistics(self, auth_client):
        d = DealershipFactory()
        resp = auth_client.get(STATS_URL.format(d.pk))
        assert resp.status_code == 200
        assert resp.data['cars_sold'] == 0
        assert resp.data['revenue'] == '0.00'

    def test_statistics_404(self, auth_client):
        resp = auth_client.get(STATS_URL.format(99999))
        assert resp.status_code == 404


@pytest.mark.django_db
class TestDealershipInventoryAPI:
    def test_list(self, auth_client):
        DealershipInventoryFactory.create_batch(2)
        resp = auth_client.get(INV_URL)
        assert resp.status_code == 200
        assert len(resp.data['results']) == 2

    def test_create_admin(self, auth_client):
        d = DealershipFactory()
        from cars.factories import CarFactory
        c = CarFactory()
        data = {'dealership': d.pk, 'car': c.pk, 'quantity': 5, 'price_per_unit': '20000.00'}
        resp = auth_client.post(INV_URL, data, format='json')
        assert resp.status_code == 201


@pytest.mark.django_db
class TestDealershipPreferenceAPI:
    def test_list(self, auth_client):
        DealershipCarPreferenceFactory.create_batch(2)
        resp = auth_client.get(PREF_URL)
        assert resp.status_code == 200

    def test_create_admin(self, auth_client):
        d = DealershipFactory()
        from cars.factories import CarFactory
        c = CarFactory()
        data = {'dealership': d.pk, 'car': c.pk, 'min_stock': 3, 'target_stock': 8}
        resp = auth_client.post(PREF_URL, data, format='json')
        assert resp.status_code == 201


@pytest.mark.django_db
class TestSaleRecordAPI:
    def test_list(self, auth_client):
        SaleRecordFactory.create_batch(2)
        resp = auth_client.get(SALE_URL)
        assert resp.status_code == 200
        assert len(resp.data['results']) == 2

    def test_create_not_allowed(self, auth_client):
        resp = auth_client.post(SALE_URL, {}, format='json')
        assert resp.status_code == 405


@pytest.mark.django_db
class TestPurchaseLogAPI:
    def test_list_admin_only(self, auth_client, buyer_auth_client):
        PurchaseLogFactory()
        assert auth_client.get(PURCH_URL).status_code == 200
        assert buyer_auth_client.get(PURCH_URL).status_code == 403


@pytest.mark.django_db
class TestBestSupplierAPI:
    def test_list(self, auth_client):
        DealershipBestSupplierFactory()
        resp = auth_client.get(BEST_URL)
        assert resp.status_code == 200
