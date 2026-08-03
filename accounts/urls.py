from django.urls import path

from accounts.views import (
    EmailChangeConfirmView,
    EmailChangeRequestView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    ResendVerificationView,
    VerifyEmailView,
)

urlpatterns = [
    # Регистрация верификация ресенд email
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path(
        "auth/resend-verification/",
        ResendVerificationView.as_view(),
        name="auth-resend-verification",
    ),
    # Пароль
    path("auth/password/change/", PasswordChangeView.as_view(), name="auth-password-change"),
    path("auth/password/reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    # Профиль
    path("auth/profile/", ProfileView.as_view(), name="auth-profile"),
    # Смена email
    path("auth/email/change/", EmailChangeRequestView.as_view(), name="auth-email-change"),
    path("auth/email/confirm/", EmailChangeConfirmView.as_view(), name="auth-email-confirm"),
]
