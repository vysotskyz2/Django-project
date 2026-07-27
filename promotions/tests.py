import pytest
from promotions.factories import PromotionFactory
from dealerships.factories import DealershipFactory

PROMO_URL = '/api/v1/promotions/'


def _url(pk):
    return f'{PROMO_URL}{pk}/'


@pytest.mark.django_db
class TestPromotionAPI:
    def test_list(self, auth_client):
        PromotionFactory.create_batch(2)
        resp = auth_client.get(PROMO_URL)
        assert resp.status_code == 200
        assert len(resp.data['results']) == 2

    def test_create_admin(self, auth_client):
        d = DealershipFactory()
        data = {
            'dealership': d.pk, 'title': 'Winter sale', 'type': 'seasonal',
            'discount_percent': '10.00',
            'start_date': '2026-11-01', 'end_date': '2026-12-31',
        }
        resp = auth_client.post(PROMO_URL, data, format='json')
        assert resp.status_code == 201

    def test_update_admin(self, auth_client):
        p = PromotionFactory()
        resp = auth_client.patch(_url(p.pk), {'discount_percent': '20.00'}, format='json')
        assert resp.status_code == 200

    def test_destroy_admin(self, auth_client):
        p = PromotionFactory()
        resp = auth_client.delete(_url(p.pk))
        assert resp.status_code == 204
