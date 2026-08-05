from rest_framework import serializers

from cars.models import Car


class CarSerializer(serializers.ModelSerializer):
    brand_display = serializers.CharField(source="get_brand_display", read_only=True)
    color_display = serializers.CharField(source="get_color_display", read_only=True)
    transmission_display = serializers.CharField(source="get_transmission_display", read_only=True)
    fuel_type_display = serializers.CharField(source="get_fuel_type_display", read_only=True)

    class Meta:
        model = Car
        fields = [
            "id",
            "brand",
            "brand_display",
            "model_name",
            "year",
            "color",
            "color_display",
            "transmission",
            "transmission_display",
            "fuel_type",
            "fuel_type_display",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
