import uuid
from datetime import timedelta
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

def get_24h():
    return timezone.now() + timedelta(hours=24)

def get_1h():
    return timezone.now() + timedelta(hours=1)


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification_token',
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=get_24h)

    class Meta:
        verbose_name = 'Email verification token'
        verbose_name_plural = 'Email verification tokens'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f'VerificationToken({self.user.username})'


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=get_1h)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Password reset token'
        verbose_name_plural = 'Password reset tokens'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f'PasswordResetToken({self.user.username})'


class EmailChangeToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_change_tokens',
    )
    new_email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=get_24h)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Email change token'
        verbose_name_plural = 'Email change tokens'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f'EmailChangeToken({self.user.username} - {self.new_email})'
