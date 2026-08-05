from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    EmailChangeConfirmSerializer,
    EmailChangeRequestSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserProfileSerializer,
)
from accounts.services import AuthService, EmailChangeService, PasswordService, ProfileService


@extend_schema(tags=["Auth"])
class RegisterView(APIView):
    """
    Создаёт пользователя и отправляет письмо с подтверждением.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Регистрация",
        request=RegisterSerializer,
        responses={201: {"description": "Пользователь создан, письмо отправлено"}},
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService().register(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        return Response(
            {"detail": "Аккаунт создан. Проверьте почту для подтверждения email."},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Auth"])
class VerifyEmailView(APIView):
    """
    Активирует аккаунт по токену из письма.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Подтверждение email",
        responses={
            200: {"description": "Email подтверждён"},
            400: {"description": "Токен недействителен или истёк"},
        },
    )
    def get(self, request: Request) -> Response:
        token = request.query_params.get("token")
        if not token:
            return Response({"detail": "Токен не передан."}, status=status.HTTP_400_BAD_REQUEST)

        AuthService().verify_email(token)
        return Response({"detail": "Email успешно подтверждён. Теперь вы можете войти."})


@extend_schema(tags=["Auth"])
class ResendVerificationView(APIView):
    """
    Повторно отправляет письмо с подтверждением.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Повторная отправка письма",
        request=ResendVerificationSerializer,
        responses={200: {"description": "Письмо отправлено"}},
    )
    def post(self, request: Request) -> Response:
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService().resend_verification(email=serializer.validated_data["email"])
        return Response({"detail": "Письмо с подтверждением отправлено повторно."})


@extend_schema(tags=["Auth"])
class PasswordChangeView(APIView):
    """
    Меняет пароль авторизованного пользователя.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Смена пароля",
        request=PasswordChangeSerializer,
        responses={200: {"description": "Пароль изменён"}},
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        PasswordService().change_password(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
        )
        return Response({"detail": "Пароль успешно изменён."})


@extend_schema(tags=["Auth"])
class PasswordResetRequestView(APIView):
    """
    Отправляет письмо со ссылкой для сброса пароля.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Запрос сброса пароля",
        request=PasswordResetRequestSerializer,
        responses={200: {"description": "Письмо отправлено"}},
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        PasswordService().request_reset(email=serializer.validated_data["email"])
        return Response({"detail": "Письмо со ссылкой для сброса пароля отправлено."})


@extend_schema(tags=["Auth"])
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Подтверждение сброса пароля",
        request=PasswordResetConfirmSerializer,
        responses={
            200: {"description": "Пароль изменён"},
            400: {"description": "Токен недействителен или истёк"},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        PasswordService().confirm_reset(
            token=str(serializer.validated_data["token"]),
            new_password=serializer.validated_data["new_password"],
        )
        return Response({"detail": "Пароль успешно изменён."})


@extend_schema(tags=["Auth"])
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Просмотр профиля", responses={200: UserProfileSerializer})
    def get(self, request: Request) -> Response:
        return Response(UserProfileSerializer(request.user).data)

    @extend_schema(
        summary="Редактирование профиля",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
    )
    def patch(self, request: Request) -> Response:
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = ProfileService().update(
            user=request.user,
            data=serializer.validated_data,
        )
        return Response(UserProfileSerializer(updated_user).data)


@extend_schema(tags=["Auth"])
class EmailChangeRequestView(APIView):
    """
    Отправляет письмо на новый адрес для подтверждения смены email.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Запрос смены email",
        request=EmailChangeRequestSerializer,
        responses={200: {"description": "Письмо отправлено на новый адрес"}},
    )
    def post(self, request: Request) -> Response:
        serializer = EmailChangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        EmailChangeService().request_change(
            user=request.user,
            new_email=serializer.validated_data["new_email"],
        )
        return Response(
            {
                "detail": f"Письмо с подтверждением отправлено на {serializer.validated_data['new_email']}."
            }
        )


@extend_schema(tags=["Auth"])
class EmailChangeConfirmView(APIView):
    """
    Применяет новый email после перехода по ссылке из письма.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Подтверждение смены email",
        responses={
            200: {"description": "Email изменён"},
            400: {"description": "Токен недействителен или истёк"},
        },
    )
    def get(self, request: Request) -> Response:
        token = request.query_params.get("token")
        if not token:
            return Response({"detail": "Токен не передан."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = EmailChangeConfirmSerializer(data={"token": token})
        serializer.is_valid(raise_exception=True)

        new_email = EmailChangeService().confirm_change(
            token=str(serializer.validated_data["token"]),
        )
        return Response({"detail": f"Email успешно изменён на {new_email}."})
