from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from buyers.models import Buyer, BuyerCarPreference
from cars.serializers import CarSerializer


class BuyerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    is_email_verified = serializers.BooleanField(read_only=True)
    balance = MoneyField(max_digits=14, decimal_places=2)
    balance_currency = serializers.CharField(read_only=True)

    class Meta:
        model = Buyer
        fields = [
            'id',
            'username',
            'email',
            'is_email_verified',
            'balance',
            'balance_currency',
            'is_deleted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'username', 'email', 'is_email_verified', 'created_at', 'updated_at']


class BuyerCarPreferenceSerializer(serializers.ModelSerializer):
    buyer_username = serializers.CharField(source='buyer.user.username', read_only=True)
    car_detail = CarSerializer(source='car', read_only=True)
    max_price = MoneyField(max_digits=14, decimal_places=2)
    max_price_currency = serializers.CharField(read_only=True)

    class Meta:
        model = BuyerCarPreference
        fields = [
            'id',
            'buyer',
            'buyer_username',
            'car',
            'car_detail',
            'max_price',
            'max_price_currency',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'buyer_username', 'created_at', 'updated_at']
