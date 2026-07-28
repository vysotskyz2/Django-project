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
            'user',
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


class BuyerPurchaseItemSerializer(serializers.Serializer):
    offer_id = serializers.IntegerField()
    car_id = serializers.IntegerField()
    car = serializers.CharField()
    dealership_id = serializers.IntegerField(allow_null=True)
    dealership_name = serializers.CharField(allow_null=True)
    quantity = serializers.IntegerField()
    price_per_unit = serializers.DecimalField(max_digits=14, decimal_places=2)
    price_per_unit_currency = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_currency = serializers.CharField()
    purchased_at = serializers.DateTimeField()


class BuyerStatisticsSerializer(serializers.Serializer):
    buyer_id = serializers.IntegerField()
    username = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_spent_currency = serializers.CharField()
    purchases_count = serializers.IntegerField()
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    balance_currency = serializers.CharField()
    purchases = BuyerPurchaseItemSerializer(many=True)
