import django_filters
from dealerships.models import (
    Dealership,
    DealershipBestSupplier,
    DealershipCarPreference,
    DealershipInventory,
    PurchaseLog,
    SaleRecord,
)


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


class DealershipCarPreferenceFilter(django_filters.FilterSet):

    dealership = django_filters.NumberFilter()
    car = django_filters.NumberFilter()
    is_preferred = django_filters.BooleanFilter()

    class Meta:
        model = DealershipCarPreference
        fields = ['dealership', 'car', 'is_preferred']


class SaleRecordFilter(django_filters.FilterSet):

    dealership = django_filters.NumberFilter()
    car = django_filters.NumberFilter()
    sold_after = django_filters.DateTimeFilter(field_name='sold_at', lookup_expr='gte')
    sold_before = django_filters.DateTimeFilter(field_name='sold_at', lookup_expr='lte')

    class Meta:
        model = SaleRecord
        fields = ['dealership', 'car']


class PurchaseLogFilter(django_filters.FilterSet):

    dealership = django_filters.NumberFilter()
    supplier = django_filters.NumberFilter()
    car = django_filters.NumberFilter()
    purchased = django_filters.BooleanFilter()
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = PurchaseLog
        fields = [
            'dealership', 'supplier', 'car',
            'purchased',
        ]


class DealershipBestSupplierFilter(django_filters.FilterSet):

    dealership = django_filters.NumberFilter()
    car = django_filters.NumberFilter()
    supplier = django_filters.NumberFilter()
    has_supplier = django_filters.BooleanFilter(
        field_name='supplier', lookup_expr='isnull', exclude=True,
        label='Has a supplier assigned (False = no supplier available)',
    )
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')

    class Meta:
        model = DealershipBestSupplier
        fields = ['dealership', 'car', 'supplier']
