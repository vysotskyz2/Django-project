import django_filters
from django.utils import timezone
from suppliers.models import Supplier, SupplierInventory, SupplierPromotion


class SupplierFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='iexact')
    is_deleted = django_filters.BooleanFilter()
    balance_min = django_filters.NumberFilter(field_name='balance', lookup_expr='gte')
    balance_max = django_filters.NumberFilter(field_name='balance', lookup_expr='lte')

    class Meta:
        model = Supplier
        fields = ['name', 'country', 'is_deleted', 'balance_min', 'balance_max']


class SupplierInventoryFilter(django_filters.FilterSet):

    supplier = django_filters.NumberFilter()
    car = django_filters.NumberFilter()
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    price_min = django_filters.NumberFilter(field_name='price_per_unit', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price_per_unit', lookup_expr='lte')

    class Meta:
        model = SupplierInventory
        fields = ['supplier', 'car', 'quantity_min', 'quantity_max', 'price_min', 'price_max']


class SupplierPromotionFilter(django_filters.FilterSet):

    supplier = django_filters.NumberFilter()
    car = django_filters.NumberFilter()
    car_isnull = django_filters.BooleanFilter(
        field_name='car', lookup_expr='isnull',
        label='Global promotion (no specific car)',
    )
    discount_min = django_filters.NumberFilter(
        field_name='discount_percent', lookup_expr='gte',
    )
    discount_max = django_filters.NumberFilter(
        field_name='discount_percent', lookup_expr='lte',
    )
    is_active = django_filters.BooleanFilter(
        method='filter_is_active',
        label='Only currently active promotions (today within start_date - end_date)',
    )
    starts_after = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    ends_before = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')

    class Meta:
        model = SupplierPromotion
        fields = [
            'supplier', 'car', 'car_isnull',
            'discount_min', 'discount_max',
            'is_active', 'starts_after', 'ends_before',
        ]

    def filter_is_active(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(start_date__lte=today, end_date__gte=today)
        return queryset.exclude(start_date__lte=today, end_date__gte=today)
