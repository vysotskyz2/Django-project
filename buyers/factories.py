import factory
import factory.django
from moneyed import Money

from buyers.models import Buyer, BuyerCarPreference
from cars.factories import CarFactory


class BuyerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Buyer

    user = factory.SubFactory('dealerships.factories.UserFactory')
    balance = Money(50_000, 'USD')


class BuyerCarPreferenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BuyerCarPreference

    buyer = factory.SubFactory(BuyerFactory)
    car = factory.SubFactory(CarFactory)
    max_price = Money(25_000, 'USD')
