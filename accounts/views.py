from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import EmailVerificationToken
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
from accounts.tasks import (
    send_email_change_confirmation,
    send_password_reset_email,
    send_verification_email,
)
from accounts.models import EmailChangeToken, PasswordResetToken

@extend_schema(tags=['Auth'])
class RegisterView(APIView):
    """
    Создаёт пользователя и отправляет письмо с подтверждением.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Регистрация',
        request=RegisterSerializer,
        responses={201: {'description': 'Пользователь создан, письмо отправлено'}},
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token_obj = EmailVerificationToken.objects.create(user=user)
        send_verification_email.delay(user.pk, str(token_obj.token))
        return Response(
            {'detail': 'Аккаунт создан. Проверьте почту для подтверждения email.'},
            status=status.HTTP_201_CREATED,
        )

@extend_schema(tags=['Auth'])
class VerifyEmailView(APIView):
    """
    Активирует аккаунт по токену из письма.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Подтверждение email',
        responses={
            200: {'description': 'Email подтверждён'},
            400: {'description': 'Токен недействителен или истёк'},
        },
    )
    def get(self, request: Request) -> Response:
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'detail': 'Токен не передан.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            import uuid
            uuid.UUID(str(token))
        except ValueError:
            return Response(
                {'detail': 'Недействительный токен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_obj = EmailVerificationToken.objects.select_related('user').get(token=token)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {'detail': 'Недействительный токен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.is_expired():
            token_obj.delete()
            return Response(
                {'detail': 'Токен истёк. Запросите повторную отправку письма.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token_obj.user
        user.is_active = True
        user.save(update_fields=['is_active'])
        token_obj.delete()

        return Response({'detail': 'Email успешно подтверждён. Теперь вы можете войти.'})

@extend_schema(tags=['Auth'])
class ResendVerificationView(APIView):
    """
    Повторно отправляет письмо с подтверждением.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Повторная отправка письма',
        request=ResendVerificationSerializer,
        responses={200: {'description': 'Письмо отправлено'}},
    )
    def post(self, request: Request) -> Response:
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.get_user()
        if user is None:
            return Response({'detail': 'Письмо отправлено'})

        EmailVerificationToken.objects.filter(user=user).delete()
        token_obj = EmailVerificationToken.objects.create(user=user)
        send_verification_email.delay(user.pk, str(token_obj.token))

        return Response({'detail': 'Письмо с подтверждением отправлено повторно.'})


@extend_schema(tags=['Auth'])
class PasswordChangeView(APIView):
    """
    Меняет пароль авторизованного пользователя.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Смена пароля',
        request=PasswordChangeSerializer,
        responses={200: {'description': 'Пароль изменён'}},
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        return Response({'detail': 'Пароль успешно изменён.'})


@extend_schema(tags=['Auth'])
class PasswordResetRequestView(APIView):
    """
    Отправляет письмо со ссылкой для сброса пароля.
    """
    permission_classes = [AllowAny]
    @extend_schema(
        summary='Запрос сброса пароля',
        request=PasswordResetRequestSerializer,
        responses={200: {'description': 'Письмо отправлено'}},
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.get_user()
        token_obj = PasswordResetToken.objects.create(user=user)
        send_password_reset_email.delay(user.pk, str(token_obj.token))

        return Response({'detail': 'Письмо со ссылкой для сброса пароля отправлено.'})


@extend_schema(tags=['Auth'])
class PasswordResetConfirmView(APIView):
    """
    Устанавливает новый пароль по токену из письма.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Подтверждение сброса пароля',
        request=PasswordResetConfirmSerializer,
        responses={
            200: {'description': 'Пароль изменён'},
            400: {'description': 'Токен недействителен или истёк'},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_token = serializer.validated_data['reset_token']
        user = reset_token.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        reset_token.is_used = True
        reset_token.save(update_fields=['is_used'])

        return Response({'detail': 'Пароль успешно изменён.'})


@extend_schema(tags=['Auth'])
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Просмотр профиля', responses={200: UserProfileSerializer})
    def get(self, request: Request) -> Response:
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary='Редактирование профиля',
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
    )
    def patch(self, request: Request) -> Response:
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(tags=['Auth'])
class EmailChangeRequestView(APIView):
    """
    Отправляет письмо на новый адрес для подтверждения смены email.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Запрос смены email',
        request=EmailChangeRequestSerializer,
        responses={200: {'description': 'Письмо отправлено на новый адрес'}},
    )
    def post(self, request: Request) -> Response:
        serializer = EmailChangeRequestSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        new_email = serializer.validated_data['new_email']
        EmailChangeToken.objects.filter(user=request.user, is_used=False).delete()

        token_obj = EmailChangeToken.objects.create(user=request.user, new_email=new_email)
        send_email_change_confirmation.delay(request.user.pk, new_email, str(token_obj.token))

        return Response({'detail': f'Письмо с подтверждением отправлено на {new_email}.'})


@extend_schema(tags=['Auth'])
class EmailChangeConfirmView(APIView):
    """
    Применяет новый email после перехода по ссылке из письма.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Подтверждение смены email',
        responses={
            200: {'description': 'Email изменён'},
            400: {'description': 'Токен недействителен или истёк'},
        },
    )
    def get(self, request: Request) -> Response:
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'detail': 'Токен не передан.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EmailChangeConfirmSerializer(data={'token': token})
        serializer.is_valid(raise_exception=True)

        change_token = serializer.get_change_token()
        user = change_token.user
        user.email = change_token.new_email
        user.save(update_fields=['email'])

        change_token.is_used = True
        change_token.save(update_fields=['is_used'])

        return Response({'detail': f'Email успешно изменён на {user.email}.'})
