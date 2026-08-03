import pytest

from cars.factories import CarFactory
from cars.models import Car

LIST_URL = "/api/v1/cars/"


def detail_url(pk):
    return f"{LIST_URL}{pk}/"


@pytest.mark.django_db
class TestCarAPI:
    def test_list_cars(self, auth_client):
        CarFactory.create_batch(3)
        resp = auth_client.get(LIST_URL)
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 3

    def test_create_car_requires_admin(self, api_client, admin_user, auth_client):
        data = {
            "brand": "toyota",
            "model_name": "Test",
            "year": 2024,
            "color": "black",
            "transmission": "automatic",
            "fuel_type": "petrol",
        }
        resp = auth_client.post(LIST_URL, data, format="json")
        assert resp.status_code == 201
        assert Car.objects.count() == 1

    def test_create_car_denied_for_non_admin(self, buyer_auth_client):
        data = {
            "brand": "toyota",
            "model_name": "Test",
            "year": 2024,
            "color": "black",
            "transmission": "automatic",
            "fuel_type": "petrol",
        }
        resp = buyer_auth_client.post(LIST_URL, data, format="json")
        assert resp.status_code == 403

    def test_list_unauthenticated(self, api_client):
        CarFactory()
        resp = api_client.get(LIST_URL)
        assert resp.status_code == 401

    def test_retrieve_car(self, auth_client):
        car = CarFactory()
        resp = auth_client.get(detail_url(car.pk))
        assert resp.status_code == 200
        assert resp.data["id"] == car.pk

    def test_update_car_admin(self, auth_client):
        car = CarFactory()
        resp = auth_client.patch(detail_url(car.pk), {"model_name": "Updated"}, format="json")
        assert resp.status_code == 200
        car.refresh_from_db()
        assert car.model_name == "Updated"

    def test_destroy_car_soft(self, auth_client):
        car = CarFactory()
        resp = auth_client.delete(detail_url(car.pk))
        assert resp.status_code == 204
        car.refresh_from_db()
        assert car.is_deleted is True
        assert Car.objects.filter(is_deleted=False).count() == 0

    def test_filter_by_brand(self, auth_client):
        CarFactory(brand="toyota")
        CarFactory(brand="bmw")
        resp = auth_client.get(f"{LIST_URL}?brand=toyota")
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1
