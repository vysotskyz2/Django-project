import django_filters
from buyers.models import Buyer, BuyerCarPreference


class BuyerFilter(django_filters.FilterSet):
    is_email_verified = django_filters.BooleanFilter(
        field_name='user__is_active',
        label='Email verified',
    )
    has_balance = django_filters.BooleanFilter(
        method='filter_has_balance',
        label='Has non-zero balance',
    )

    def filter_has_balance(self, queryset, name, value):
        if value:
            return queryset.filter(balance__gt=0)
        return queryset.filter(balance__lte=0)

    class Meta:
        model = Buyer
        fields = ['is_deleted']


class BuyerCarPreferenceFilter(django_filters.FilterSet):
    buyer = django_filters.NumberFilter()
    car = django_filters.NumberFilter()

    class Meta:
        model = BuyerCarPreference
        fields = ['buyer', 'car']
