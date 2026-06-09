from django_countries.serializer_fields import CountryField
from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from cars.serializers import CarSerializer
from dealerships.models import Dealership, DealershipInventory


class DealershipSerializer(serializers.ModelSerializer):

    location = CountryField(name_only=True)
    balance = MoneyField(max_digits=14, decimal_places=2)
    balance_currency = serializers.CharField(read_only=True)

    class Meta:
        model = Dealership
        fields = [
            'id',
            'name',
            'location',
            'balance',
            'balance_currency',
            'is_deleted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DealershipInventorySerializer(serializers.ModelSerializer):

    car_detail = CarSerializer(source='car', read_only=True)
    dealership_name = serializers.CharField(source='dealership.name', read_only=True)
    price_per_unit = MoneyField(max_digits=14, decimal_places=2)
    price_per_unit_currency = serializers.CharField(read_only=True)

    class Meta:
        model = DealershipInventory
        fields = [
            'id',
            'dealership',
            'dealership_name',
            'car',
            'car_detail',
            'quantity',
            'price_per_unit',
            'price_per_unit_currency',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
