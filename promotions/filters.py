import django_filters
from promotions.models import Promotion, PromotionType


class PromotionFilter(django_filters.FilterSet):

    dealership = django_filters.NumberFilter()
    type = django_filters.MultipleChoiceFilter(choices=PromotionType.choices)
    title = django_filters.CharFilter(lookup_expr='icontains')
    discount_min = django_filters.NumberFilter(field_name='discount_percent', lookup_expr='gte')
    discount_max = django_filters.NumberFilter(field_name='discount_percent', lookup_expr='lte')
    start_date_after = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_before = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date_after = django_filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date_before = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')
    is_active = django_filters.BooleanFilter(method='filter_is_active', label='Активная акция')

    class Meta:
        model = Promotion
        fields = [
            'dealership',
            'type',
            'title',
            'discount_min', 'discount_max',
            'start_date_after', 'start_date_before',
            'end_date_after', 'end_date_before',
            'is_active',
        ]

    def filter_is_active(self, queryset, name, value):
        from django.utils import timezone
        today = timezone.now().date()
        if value:
            return queryset.filter(start_date__lte=today, end_date__gte=today)
        return queryset.exclude(start_date__lte=today, end_date__gte=today)
