from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from accounts.models import EmailChangeToken, PasswordResetToken

class RegisterSerializer(serializers.ModelSerializer):
    """Создание нового пользователя."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label='Confirm password',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('email обязателен.')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Пароли не совпадают.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False,
        )
        return user

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь с таким email не найден.')

        if user.is_active:
            raise serializers.ValidationError('Этот email уже подтверждён.')

        self._user = user
        return value

    def get_user(self):
        return getattr(self, '_user', None)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, label='Confirm new password')

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Пароли не совпадают.'})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь с таким email не найден.')

        if not user.is_active:
            raise serializers.ValidationError('Аккаунт не активирован. Сначала подтвердите email.')

        self._user = user
        return value

    def get_user(self):
        return getattr(self, '_user', None)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, label='Confirm new password')

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Пароли не совпадают.'})

        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(
                token=attrs['token'],
                is_used=False,
            )
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({'token': 'Недействительный токен.'})

        if reset_token.is_expired():
            raise serializers.ValidationError({'token': 'Токен истёк. Запросите сброс пароля снова.'})

        attrs['reset_token'] = reset_token
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    """Просмотр и редактирование профиля. Email — только для чтения, меняется отдельным эндпоинтом."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')
        read_only_fields = ('id', 'email', 'is_active', 'date_joined')

    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError('Этот username уже занят.')
        return value

class EmailChangeRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        user = self.context['request'].user
        if user.email == value:
            raise serializers.ValidationError('Новый email совпадает с текущим.')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Этот email уже используется другим пользователем.')
        return value

class EmailChangeConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            change_token = EmailChangeToken.objects.select_related('user').get(
                token=value,
                is_used=False,
            )
        except EmailChangeToken.DoesNotExist:
            raise serializers.ValidationError('Недействительный токен.')

        if change_token.is_expired():
            raise serializers.ValidationError('Токен истёк. Запросите смену email снова.')

        self._change_token = change_token
        return value

    def get_change_token(self):
        return getattr(self, '_change_token', None)
