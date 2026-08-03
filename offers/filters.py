import django_filters

from offers.models import Offer, OfferStatus


class OfferFilter(django_filters.FilterSet):
    dealership = django_filters.NumberFilter()
    supplier = django_filters.NumberFilter()
    car = django_filters.NumberFilter()
    status = django_filters.MultipleChoiceFilter(choices=OfferStatus.choices)
    is_deleted = django_filters.BooleanFilter()
    quantity_min = django_filters.NumberFilter(field_name="quantity", lookup_expr="gte")
    quantity_max = django_filters.NumberFilter(field_name="quantity", lookup_expr="lte")
    price_min = django_filters.NumberFilter(field_name="offered_price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="offered_price", lookup_expr="lte")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Offer
        fields = [
            "dealership",
            "supplier",
            "car",
            "status",
            "is_deleted",
            "quantity_min",
            "quantity_max",
            "price_min",
            "price_max",
            "created_after",
            "created_before",
        ]
