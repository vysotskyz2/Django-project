import django_filters
from cars.models import Brand, Car, Color, FuelType, Transmission


class CarFilter(django_filters.FilterSet):

    brand = django_filters.MultipleChoiceFilter(choices=Brand.choices)
    color = django_filters.MultipleChoiceFilter(choices=Color.choices)
    transmission = django_filters.MultipleChoiceFilter(choices=Transmission.choices)
    fuel_type = django_filters.MultipleChoiceFilter(choices=FuelType.choices)
    year_min = django_filters.NumberFilter(field_name='year', lookup_expr='gte')
    year_max = django_filters.NumberFilter(field_name='year', lookup_expr='lte')
    is_deleted = django_filters.BooleanFilter()

    class Meta:
        model = Car
        fields = ['brand', 'color', 'transmission', 'fuel_type', 'year_min', 'year_max', 'is_deleted']
