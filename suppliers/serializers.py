from django_countries.serializer_fields import CountryField
from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from cars.serializers import CarSerializer
from suppliers.models import Supplier, SupplierInventory


class SupplierSerializer(serializers.ModelSerializer):

    country = CountryField(name_only=True)
    balance = MoneyField(max_digits=14, decimal_places=2)
    balance_currency = serializers.CharField(read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'country',
            'balance', 'balance_currency',
            'is_deleted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SupplierInventorySerializer(serializers.ModelSerializer):

    car_detail = CarSerializer(source='car', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    price_per_unit = MoneyField(max_digits=14, decimal_places=2)
    price_per_unit_currency = serializers.CharField(read_only=True)

    class Meta:
        model = SupplierInventory
        fields = [
            'id',
            'supplier',
            'supplier_name',
            'car',
            'car_detail',
            'quantity',
            'price_per_unit',
            'price_per_unit_currency',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
