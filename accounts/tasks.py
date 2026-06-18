from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_verification_email(user_id: int, token: str) -> None:
    """Отправляет письмо с ссылкой для подтверждения email после регистрации."""
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    verify_url = f"{settings.FRONTEND_URL}/api/v1/auth/verify-email/?token={token}"

    send_mail(
        subject="Подтвердите ваш email",
        message=(
            f"Привет, {user.username}!\n\n"
            f"Для активации аккаунта перейдите по ссылке:\n{verify_url}\n\n"
            f"Ссылка действительна 24 часа.\n\n"
            f"Если вы не регистрировались — просто проигнорируйте это письмо."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@shared_task
def send_password_reset_email(user_id: int, token: str) -> None:
    """Отправляет письмо со ссылкой для сброса пароля."""
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    reset_url = f"{settings.FRONTEND_URL}/api/v1/auth/password/reset/confirm/?token={token}"

    send_mail(
        subject="Сброс пароля",
        message=(
            f"Привет, {user.username}!\n\n"
            f"Для сброса пароля перейдите по ссылке:\n{reset_url}\n\n"
            f"Ссылка действительна 1 час.\n\n"
            f"Если вы не запрашивали сброс пароля — просто проигнорируйте это письмо."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@shared_task
def send_email_change_confirmation(user_id: int, new_email: str, token: str) -> None:
    """Отправляет письмо на новый адрес для подтверждения смены email."""
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    confirm_url = f"{settings.FRONTEND_URL}/api/v1/auth/email/confirm/?token={token}"

    send_mail(
        subject="Подтвердите смену email",
        message=(
            f"Привет, {user.username}!\n\n"
            f"Вы запросили смену email-адреса на {new_email}.\n"
            f"Для подтверждения перейдите по ссылке:\n{confirm_url}\n\n"
            f"Ссылка действительна 24 часа.\n\n"
            f"Если вы не запрашивали смену email — просто проигнорируйте это письмо."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[new_email],
        fail_silently=False,
    )
