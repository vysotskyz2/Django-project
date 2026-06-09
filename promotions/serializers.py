from rest_framework import serializers
from dealerships.serializers import DealershipSerializer
from promotions.models import Promotion, PromotionType


class PromotionSerializer(serializers.ModelSerializer):

    dealership_detail = DealershipSerializer(source='dealership', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Promotion
        fields = [
            'id',
            'dealership',
            'dealership_detail',
            'title',
            'description',
            'type',
            'type_display',
            'discount_percent',
            'start_date','end_date',
            'created_at','updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {'end_date': 'Дата окончания не может быть раньше даты начала.'}
            )
        return attrs
