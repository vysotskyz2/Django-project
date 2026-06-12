from djmoney.contrib.django_rest_framework import MoneyField
from rest_framework import serializers
from cars.serializers import CarSerializer
from dealerships.serializers import DealershipSerializer
from suppliers.serializers import SupplierSerializer
from offers.models import Offer, OfferStatus


class OfferSerializer(serializers.ModelSerializer):

    dealership_detail = DealershipSerializer(source='dealership', read_only=True)
    supplier_detail = SupplierSerializer(source='supplier', read_only=True)
    car_detail = CarSerializer(source='car', read_only=True)
    offered_price = MoneyField(max_digits=14, decimal_places=2)
    offered_price_currency = serializers.CharField(read_only=True)
    max_budget = MoneyField(max_digits=14, decimal_places=2)
    max_budget_currency = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'dealership',
            'dealership_detail',
            'supplier',
            'supplier_detail',
            'car',
            'car_detail',
            'quantity',
            'offered_price',
            'offered_price_currency',
            'max_budget',
            'max_budget_currency',
            'status',
            'status_display',
            'is_deleted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OfferStatusUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Offer
        fields = ['status']

    def validate_status(self, value):
        allowed = [OfferStatus.ACCEPTED, OfferStatus.REJECTED, OfferStatus.CANCELLED]
        if value not in allowed:
            raise serializers.ValidationError(
                f'Недопустимый статус. Выберите один из: {", ".join(allowed)}'
            )
        return value
