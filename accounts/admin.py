from django.contrib import admin
from accounts.models import EmailChangeToken, EmailVerificationToken, PasswordResetToken

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_expired_display')
    readonly_fields = ('user', 'token', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email')

    @admin.display(boolean=True, description='Истёк?')
    def is_expired_display(self, obj):
        return obj.is_expired()


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_used', 'is_expired_display')
    readonly_fields = ('user', 'token', 'created_at', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('user__username', 'user__email')

    @admin.display(boolean=True, description='Истёк?')
    def is_expired_display(self, obj):
        return obj.is_expired()


@admin.register(EmailChangeToken)
class EmailChangeTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'new_email', 'created_at', 'expires_at', 'is_used', 'is_expired_display')
    readonly_fields = ('user', 'token', 'new_email', 'created_at', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('user__username', 'user__email', 'new_email')

    @admin.display(boolean=True, description='Истёк?')
    def is_expired_display(self, obj):
        return obj.is_expired()
