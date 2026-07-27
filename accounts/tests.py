import pytest
from accounts.models import EmailVerificationToken
from dealerships.factories import UserFactory
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User


REGISTER_URL = '/api/v1/auth/register/'
VERIFY_URL = '/api/v1/auth/verify-email/'
RESEND_URL = '/api/v1/auth/resend-verification/'
PASSWORD_CHANGE_URL = '/api/v1/auth/password/change/'
PASSWORD_RESET_URL = '/api/v1/auth/password/reset/'
PASSWORD_RESET_CONFIRM_URL = '/api/v1/auth/password/reset/confirm/'
PROFILE_URL = '/api/v1/auth/profile/'
EMAIL_CHANGE_URL = '/api/v1/auth/email/change/'
EMAIL_CHANGE_CONFIRM_URL = '/api/v1/auth/email/confirm/'


@pytest.mark.django_db
class TestAuthAPI:
    def test_register(self, api_client):
        data = {
            'username': 'newuser', 'email': 'new@test.com',
            'password': 'StrongPass123!', 'password2': 'StrongPass123!',
        }
        resp = api_client.post(REGISTER_URL, data, format='json')
        assert resp.status_code == 201
        assert EmailVerificationToken.objects.count() == 1

    def test_register_password_mismatch(self, api_client):
        data = {
            'username': 'newuser', 'email': 'new@test.com',
            'password': 'StrongPass123!', 'password2': 'WrongPass123!',
        }
        resp = api_client.post(REGISTER_URL, data, format='json')
        assert resp.status_code == 400

    def test_verify_email(self, api_client):
        self.test_register(api_client)
        token = EmailVerificationToken.objects.first()
        resp = api_client.get(f'{VERIFY_URL}?token={token.token}')
        assert resp.status_code == 200

    def test_verify_email_missing_token(self, api_client):
        resp = api_client.get(VERIFY_URL)
        assert resp.status_code == 400

    def test_resend_verification(self, api_client):
        self.test_register(api_client)
        resp = api_client.post(RESEND_URL, {'email': 'new@test.com'}, format='json')
        assert resp.status_code == 200

    def test_password_change(self, api_client):
        self.test_register(api_client)
        token = EmailVerificationToken.objects.first()
        api_client.get(f'{VERIFY_URL}?token={token.token}')

        user = User.objects.get(username='newuser')
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        data = {
            'old_password': 'StrongPass123!',
            'new_password': 'NewStrongPass123!',
            'new_password2': 'NewStrongPass123!',
        }
        resp = api_client.post(PASSWORD_CHANGE_URL, data, format='json')
        assert resp.status_code == 200

    def test_password_reset_request(self, api_client):
        UserFactory(email='reset@test.com', username='resetuser')
        resp = api_client.post(PASSWORD_RESET_URL, {'email': 'reset@test.com'}, format='json')
        assert resp.status_code == 200

    def test_profile_retrieve(self, auth_client):
        resp = auth_client.get(PROFILE_URL)
        assert resp.status_code == 200
        assert resp.data['username'] == 'admin'

    def test_profile_update(self, auth_client):
        resp = auth_client.patch(PROFILE_URL, {'first_name': 'John'}, format='json')
        assert resp.status_code == 200
        assert resp.data['first_name'] == 'John'

    def test_profile_unauthenticated(self, api_client):
        resp = api_client.get(PROFILE_URL)
        assert resp.status_code == 401
