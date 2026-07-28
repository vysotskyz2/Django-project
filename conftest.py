import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from dealerships.factories import UserFactory
from buyers.factories import BuyerFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return UserFactory(username='admin', is_staff=True)


@pytest.fixture
def buyer_user():
    return BuyerFactory()


@pytest.fixture
def auth_client(admin_user):
    client = APIClient()
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def buyer_auth_client(buyer_user):
    client = APIClient()
    refresh = RefreshToken.for_user(buyer_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client
