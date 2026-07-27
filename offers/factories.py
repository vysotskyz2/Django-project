import factory
import factory.django
from moneyed import Money

from offers.models import Offer, OfferStatus
from cars.factories import CarFactory


class OfferFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Offer

    buyer = factory.SubFactory('buyers.factories.BuyerFactory')
    dealership = factory.SubFactory('dealerships.factories.DealershipFactory')
    supplier = None
    car = factory.SubFactory(CarFactory)
    quantity = 1
    max_budget = Money(30_000, 'USD')
    status = OfferStatus.PENDING
