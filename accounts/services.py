from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from rest_framework.exceptions import ValidationError

from accounts.repositories import (
    EmailChangeTokenRepository,
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    UserRepository,
)


class EmailService:
    @staticmethod
    def send_verification(username: str, email: str, token: str) -> None:
        verify_url = f"{settings.FRONTEND_URL}/api/v1/auth/verify-email/?token={token}"
        send_mail(
            subject="Подтвердите ваш email",
            message=(
                f"Привет, {username}!\n\n"
                f"Для активации аккаунта перейдите по ссылке:\n{verify_url}\n\n"
                f"Ссылка действительна 24 часа.\n\n"
                f"Если вы не регистрировались - просто проигнорируйте это письмо."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

    @staticmethod
    def send_password_reset(username: str, email: str, token: str) -> None:
        reset_url = f"{settings.FRONTEND_URL}/api/v1/auth/password/reset/confirm/?token={token}"
        send_mail(
            subject="Сброс пароля",
            message=(
                f"Привет, {username}!\n\n"
                f"Для сброса пароля перейдите по ссылке:\n{reset_url}\n\n"
                f"Ссылка действительна 1 час.\n\n"
                f"Если вы не запрашивали сброс пароля - просто проигнорируйте это письмо."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

    @staticmethod
    def send_email_change_confirmation(username: str, new_email: str, token: str) -> None:
        confirm_url = f"{settings.FRONTEND_URL}/api/v1/auth/email/confirm/?token={token}"
        send_mail(
            subject="Подтвердите смену email",
            message=(
                f"Привет, {username}!\n\n"
                f"Вы запросили смену email-адреса на {new_email}.\n"
                f"Для подтверждения перейдите по ссылке:\n{confirm_url}\n\n"
                f"Ссылка действительна 24 часа.\n\n"
                f"Если вы не запрашивали смену email - просто проигнорируйте это письмо."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[new_email],
            fail_silently=False,
        )


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.verification_token_repo = EmailVerificationTokenRepository()

    def register(self, username: str, email: str, password: str) -> User:
        from accounts.tasks import send_verification_email

        if self.user_repo.username_exists(username):
            raise ValidationError({"username": "Пользователь с таким именем уже существует."})
        if self.user_repo.email_exists(email):
            raise ValidationError({"email": "Пользователь с таким email уже зарегистрирован."})
        user = self.user_repo.create(username, email, password)
        token_obj = self.verification_token_repo.create(user)
        send_verification_email.delay(user.username, user.email, str(token_obj.token))
        return user

    def verify_email(self, token: str) -> None:
        token_obj = self.verification_token_repo.get_by_token(token)
        if token_obj is None:
            raise ValidationError("Недействительный токен.")

        if token_obj.is_expired():
            self.verification_token_repo.delete(token_obj)
            raise ValidationError("Токен истёк. Запросите повторную отправку письма.")
        with transaction.atomic():
            self.user_repo.activate(token_obj.user)
            self.verification_token_repo.delete(token_obj)

    def resend_verification(self, email: str) -> None:
        from accounts.tasks import send_verification_email

        user = self.user_repo.get_by_email(email)
        if user is None:
            raise ValidationError("Пользователь с таким email не найден.")
        if user.is_active:
            raise ValidationError("Этот email уже подтверждён.")

        self.verification_token_repo.delete_for_user(user)
        token_obj = self.verification_token_repo.create(user)
        send_verification_email.delay(user.username, user.email, str(token_obj.token))


class PasswordService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.reset_token_repo = PasswordResetTokenRepository()

    def change_password(self, user: User, new_password: str) -> None:
        self.user_repo.set_password(user, new_password)

    def request_reset(self, email: str) -> None:
        user = self.user_repo.get_by_email(email)
        if user is None:
            raise ValidationError("Пользователь с таким email не найден.")
        if not user.is_active:
            raise ValidationError("Аккаунт не активирован. Сначала подтвердите email.")

        from accounts.tasks import send_password_reset_email

        token_obj = self.reset_token_repo.create(user)
        send_password_reset_email.delay(user.username, user.email, str(token_obj.token))

    def confirm_reset(self, token: str, new_password: str) -> None:
        token_obj = self.reset_token_repo.get_active_by_token(token)
        if token_obj is None:
            raise ValidationError({"token": "Недействительный токен."})

        if token_obj.is_expired():
            raise ValidationError({"token": "Токен истёк. Запросите сброс пароля снова."})
        with transaction.atomic():
            self.user_repo.set_password(token_obj.user, new_password)
            self.reset_token_repo.mark_used(token_obj)


class ProfileService:
    def __init__(self):
        self.user_repo = UserRepository()

    def update(self, user: User, data: dict) -> User:
        if "username" in data and self.user_repo.username_exists(
            data["username"], exclude_pk=user.pk
        ):
            raise ValidationError({"username": "Этот username уже занят."})
        return self.user_repo.update_profile(user, data)


class EmailChangeService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.change_token_repo = EmailChangeTokenRepository()

    def request_change(self, user: User, new_email: str) -> None:
        if user.email == new_email:
            raise ValidationError("Новый email совпадает с текущим.")
        if self.user_repo.email_exists(new_email, exclude_pk=user.pk):
            raise ValidationError("Этот email уже используется другим пользователем.")

        from accounts.tasks import send_email_change_confirmation

        self.change_token_repo.delete_pending_for_user(user)
        token_obj = self.change_token_repo.create(user, new_email)
        send_email_change_confirmation.delay(user.username, new_email, str(token_obj.token))

    def confirm_change(self, token: str) -> str:
        token_obj = self.change_token_repo.get_active_by_token(token)
        if token_obj is None:
            raise ValidationError("Недействительный токен.")

        if token_obj.is_expired():
            raise ValidationError("Токен истёк. Запросите смену email снова.")
        with transaction.atomic():
            self.user_repo.update_email(token_obj.user, token_obj.new_email)
            self.change_token_repo.mark_used(token_obj)
        return token_obj.new_email
