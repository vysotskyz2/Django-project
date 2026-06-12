import django_filters
from dealerships.models import Dealership, DealershipInventory


class DealershipFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='iexact')
    is_deleted = django_filters.BooleanFilter()
    balance_min = django_filters.NumberFilter(field_name='balance', lookup_expr='gte')
    balance_max = django_filters.NumberFilter(field_name='balance', lookup_expr='lte')

    class Meta:
        model = Dealership
        fields = ['name', 'location', 'is_deleted', 'balance_min', 'balance_max']


class DealershipInventoryFilter(django_filters.FilterSet):

    dealership = django_filters.NumberFilter()
    car = django_filters.NumberFilter()
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    price_min = django_filters.NumberFilter(field_name='price_per_unit', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price_per_unit', lookup_expr='lte')

    class Meta:
        model = DealershipInventory
        fields = ['dealership', 'car', 'quantity_min', 'quantity_max', 'price_min', 'price_max']
