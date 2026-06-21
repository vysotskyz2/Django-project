from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError

from accounts.models import EmailChangeToken, EmailVerificationToken, PasswordResetToken


class UserRepository:
    def get_by_email(self, email: str) -> User | None:
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def create(self, username: str, email: str, password: str) -> User:
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False,
        )

    def activate(self, user: User) -> None:
        user.is_active = True
        user.save(update_fields=['is_active'])

    def set_password(self, user: User, new_password: str) -> None:
        user.set_password(new_password)
        user.save(update_fields=['password'])

    def update_email(self, user: User, new_email: str) -> None:
        user.email = new_email
        user.save(update_fields=['email'])

    def update_profile(self, user: User, data: dict) -> User:
        for field, value in data.items():
            setattr(user, field, value)
        user.save(update_fields=list(data.keys()))
        return user

    def email_exists(self, email: str, exclude_pk: int | None = None) -> bool:
        qs = User.objects.filter(email=email)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()

    def username_exists(self, username: str, exclude_pk: int | None = None) -> bool:
        qs = User.objects.filter(username=username)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()


class EmailVerificationTokenRepository:
    def create(self, user: User) -> EmailVerificationToken:
        return EmailVerificationToken.objects.create(user=user)

    def get_by_token(self, token: str) -> EmailVerificationToken | None:
        try:
            return EmailVerificationToken.objects.select_related('user').get(token=token)
        except (EmailVerificationToken.DoesNotExist, DjangoValidationError):
            return None

    def delete_for_user(self, user: User) -> None:
        EmailVerificationToken.objects.filter(user=user).delete()

    def delete(self, token_obj: EmailVerificationToken) -> None:
        token_obj.delete()


class PasswordResetTokenRepository:
    def create(self, user: User) -> PasswordResetToken:
        return PasswordResetToken.objects.create(user=user)

    def get_active_by_token(self, token: str) -> PasswordResetToken | None:
        try:
            return PasswordResetToken.objects.select_related('user').get(
                token=token,
                is_used=False,
            )
        except (PasswordResetToken.DoesNotExist, DjangoValidationError):
            return None

    def mark_used(self, token_obj: PasswordResetToken) -> None:
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])


class EmailChangeTokenRepository:
    def create(self, user: User, new_email: str) -> EmailChangeToken:
        return EmailChangeToken.objects.create(user=user, new_email=new_email)

    def get_active_by_token(self, token: str) -> EmailChangeToken | None:
        try:
            return EmailChangeToken.objects.select_related('user').get(
                token=token,
                is_used=False,
            )
        except (EmailChangeToken.DoesNotExist, DjangoValidationError):
            return None

    def delete_pending_for_user(self, user: User) -> None:
        EmailChangeToken.objects.filter(user=user, is_used=False).delete()

    def mark_used(self, token_obj: EmailChangeToken) -> None:
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])
