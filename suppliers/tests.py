import pytest
from suppliers.factories import (
    SupplierFactory,
    SupplierInventoryFactory,
    SupplierPromotionFactory,
)

SUPP_URL = '/api/v1/suppliers/'
INV_URL = '/api/v1/supplier-inventory/'
PROMO_URL = '/api/v1/supplier-promotions/'
STATS_URL = '/api/v1/suppliers/{}/statistics/'


def _url(base, pk):
    return f'{base}{pk}/'


@pytest.mark.django_db
class TestSupplierAPI:
    def test_list(self, auth_client):
        SupplierFactory.create_batch(2)
        resp = auth_client.get(SUPP_URL)
        assert resp.status_code == 200
        assert len(resp.data['results']) == 2

    def test_create_admin(self, auth_client):
        data = {'name': 'NewSupplier', 'country': 'US', 'balance': '100000.00'}
        resp = auth_client.post(SUPP_URL, data, format='json')
        assert resp.status_code == 201

    def test_soft_delete(self, auth_client):
        s = SupplierFactory()
        resp = auth_client.delete(_url(SUPP_URL, s.pk))
        assert resp.status_code == 204
        s.refresh_from_db()
        assert s.is_deleted is True

    def test_statistics(self, auth_client):
        s = SupplierFactory()
        resp = auth_client.get(STATS_URL.format(s.pk))
        assert resp.status_code == 200
        assert resp.data['deals_count'] == 0
        assert resp.data['income'] == '0.00'


@pytest.mark.django_db
class TestSupplierInventoryAPI:
    def test_list(self, auth_client):
        SupplierInventoryFactory.create_batch(2)
        resp = auth_client.get(INV_URL)
        assert resp.status_code == 200

    def test_create_admin(self, auth_client):
        s = SupplierFactory()
        from cars.factories import CarFactory
        c = CarFactory()
        data = {'supplier': s.pk, 'car': c.pk, 'quantity': 20, 'price_per_unit': '12000.00'}
        resp = auth_client.post(INV_URL, data, format='json')
        assert resp.status_code == 201


@pytest.mark.django_db
class TestSupplierPromotionAPI:
    def test_list(self, auth_client):
        SupplierPromotionFactory.create_batch(2)
        resp = auth_client.get(PROMO_URL)
        assert resp.status_code == 200

    def test_create_admin(self, auth_client):
        s = SupplierFactory()
        from cars.factories import CarFactory
        c = CarFactory()
        data = {
            'supplier': s.pk, 'car': c.pk, 'title': 'Summer sale',
            'description': 'desc', 'discount_percent': '15.00',
            'start_date': '2026-07-01', 'end_date': '2026-08-31',
        }
        resp = auth_client.post(PROMO_URL, data, format='json')
        assert resp.status_code == 201
