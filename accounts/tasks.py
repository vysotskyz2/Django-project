from celery import shared_task

from accounts.services import EmailService


@shared_task
def send_verification_email(username: str, email: str, token: str) -> None:
    """Отправляет письмо с ссылкой для подтверждения email после регистрации."""
    EmailService.send_verification(username, email, token)


@shared_task
def send_password_reset_email(username: str, email: str, token: str) -> None:
    """Отправляет письмо со ссылкой для сброса пароля."""
    EmailService.send_password_reset(username, email, token)


@shared_task
def send_email_change_confirmation(username: str, new_email: str, token: str) -> None:
    """Отправляет письмо на новый адрес для подтверждения смены email."""
    EmailService.send_email_change_confirmation(username, new_email, token)
