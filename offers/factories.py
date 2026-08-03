import factory
import factory.django
from moneyed import Money

from cars.factories import CarFactory
from offers.models import Offer, OfferStatus


class OfferFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Offer

    buyer = factory.SubFactory("buyers.factories.BuyerFactory")
    dealership = factory.SubFactory("dealerships.factories.DealershipFactory")
    supplier = None
    car = factory.SubFactory(CarFactory)
    quantity = 1
    max_budget = Money(30_000, "USD")
    status = OfferStatus.PENDING
