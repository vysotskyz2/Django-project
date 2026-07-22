from django_countries.serializer_fields import CountryField
from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from cars.serializers import CarSerializer
from dealerships.models import (
    Dealership,
    DealershipBestSupplier,
    DealershipCarPreference,
    DealershipInventory,
    PurchaseLog,
    SaleRecord,
)


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


class DealershipCarPreferenceSerializer(serializers.ModelSerializer):
    dealership_name = serializers.CharField(source='dealership.name', read_only=True)
    car_detail = CarSerializer(source='car', read_only=True)

    class Meta:
        model = DealershipCarPreference
        fields = [
            'id',
            'dealership',
            'dealership_name',
            'car',
            'car_detail',
            'min_stock',
            'target_stock',
            'is_preferred',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        min_stock = attrs.get('min_stock', getattr(self.instance, 'min_stock', None))
        target_stock = attrs.get('target_stock', getattr(self.instance, 'target_stock', None))
        if min_stock is not None and target_stock is not None and target_stock < min_stock:
            raise serializers.ValidationError(
                {'target_stock': 'target_stock must be >= min_stock.'}
            )
        return attrs


class SaleRecordSerializer(serializers.ModelSerializer):
    dealership_name = serializers.CharField(source='dealership.name', read_only=True)
    car_detail = CarSerializer(source='car', read_only=True)

    class Meta:
        model = SaleRecord
        fields = [
            'id',
            'dealership',
            'dealership_name',
            'car',
            'car_detail',
            'quantity_sold',
            'sold_at',
            'created_at',
        ]
        read_only_fields = fields


class PurchaseLogSerializer(serializers.ModelSerializer):
    dealership_name = serializers.CharField(source='dealership.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    car_detail = CarSerializer(source='car', read_only=True)
    price_per_unit = MoneyField(max_digits=14, decimal_places=2, read_only=True)
    price_per_unit_currency = serializers.CharField(read_only=True)
    total_cost = MoneyField(max_digits=14, decimal_places=2, read_only=True)
    total_cost_currency = serializers.CharField(read_only=True)

    class Meta:
        model = PurchaseLog
        fields = [
            'id',
            'dealership',
            'dealership_name',
            'supplier',
            'supplier_name',
            'car',
            'car_detail',
            'quantity',
            'price_per_unit',
            'price_per_unit_currency',
            'total_cost',
            'total_cost_currency',
            'purchased',
            'reason',
            'created_at',
        ]
        read_only_fields = fields


class DealershipBestSupplierSerializer(serializers.ModelSerializer):
    dealership_name = serializers.CharField(source='dealership.name', read_only=True)
    car_detail = CarSerializer(source='car', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, default=None)
    effective_price = MoneyField(max_digits=14, decimal_places=2, read_only=True)
    effective_price_currency = serializers.CharField(read_only=True)

    class Meta:
        model = DealershipBestSupplier
        fields = [
            'id',
            'dealership',
            'dealership_name',
            'car',
            'car_detail',
            'supplier',
            'supplier_name',
            'effective_price',
            'effective_price_currency',
            'reason',
            'updated_at',
        ]
        read_only_fields = fields


class DealershipStatisticsSerializer(serializers.Serializer):
    dealership_id = serializers.IntegerField()
    dealership_name = serializers.CharField()
    cars_sold = serializers.IntegerField()
    unique_buyers = serializers.IntegerField()
    accepted_offers = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    revenue_currency = serializers.CharField()
    purchase_spend = serializers.DecimalField(max_digits=14, decimal_places=2)
    purchase_spend_currency = serializers.CharField()
    profit = serializers.DecimalField(max_digits=14, decimal_places=2)
    profit_currency = serializers.CharField()
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    balance_currency = serializers.CharField()
    inventory_units = serializers.IntegerField()
