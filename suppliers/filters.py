import django_filters
from suppliers.models import Supplier, SupplierInventory


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
