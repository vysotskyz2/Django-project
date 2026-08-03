import pytest

from cars.factories import CarFactory
from dealerships.factories import DealershipFactory
from offers.factories import OfferFactory
from offers.models import OfferStatus

OFFER_URL = "/api/v1/offers/"


def _url(pk):
    return f"{OFFER_URL}{pk}/"


@pytest.mark.django_db
class TestOfferAPI:
    def test_list(self, auth_client):
        OfferFactory.create_batch(2)
        resp = auth_client.get(OFFER_URL)
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 2

    def test_create_requires_auth_and_email_verified(self, buyer_auth_client, api_client):
        d = DealershipFactory()
        c = CarFactory()
        data = {"dealership": d.pk, "car": c.pk, "quantity": 2, "max_budget": "30000.00"}
        resp = buyer_auth_client.post(OFFER_URL, data, format="json")
        assert resp.status_code == 201
        resp = api_client.post(OFFER_URL, data, format="json")
        assert resp.status_code == 401

    def test_retrieve(self, auth_client):
        o = OfferFactory()
        resp = auth_client.get(_url(o.pk))
        assert resp.status_code == 200

    def test_set_status_accept(self, auth_client):
        o = OfferFactory()
        resp = auth_client.patch(
            f"{_url(o.pk)}set-status/",
            {"status": OfferStatus.ACCEPTED},
            format="json",
        )
        assert resp.status_code == 200
        o.refresh_from_db()
        assert o.status == OfferStatus.ACCEPTED

    def test_set_status_reject(self, auth_client):
        o = OfferFactory()
        resp = auth_client.patch(
            f"{_url(o.pk)}set-status/",
            {"status": OfferStatus.REJECTED},
            format="json",
        )
        assert resp.status_code == 200
        o.refresh_from_db()
        assert o.status == OfferStatus.REJECTED

    def test_set_status_invalid(self, auth_client):
        o = OfferFactory()
        resp = auth_client.patch(
            f"{_url(o.pk)}set-status/",
            {"status": "invalid"},
            format="json",
        )
        assert resp.status_code == 400

    def test_soft_delete(self, auth_client):
        o = OfferFactory()
        resp = auth_client.delete(_url(o.pk))
        assert resp.status_code == 204
        o.refresh_from_db()
        assert o.is_deleted is True
