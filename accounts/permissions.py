from rest_framework.permissions import BasePermission

class IsEmailVerified(BasePermission):
    """
    Разрешает доступ только пользователям с подтверждённым email
    """
    message = 'Необходимо подтвердить email перед выполнением этого действия.'
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )
