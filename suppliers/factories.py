import factory
import factory.django
from moneyed import Money
from suppliers.models import Supplier, SupplierInventory, SupplierPromotion
from cars.factories import CarFactory


class SupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Supplier

    name = factory.Sequence(lambda n: f'Supplier-{n}')
    country = 'US'
    balance = Money(200_000, 'USD')


class SupplierInventoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupplierInventory

    supplier = factory.SubFactory(SupplierFactory)
    car = factory.SubFactory(CarFactory)
    quantity = 30
    price_per_unit = Money(15_000, 'USD')


class SupplierPromotionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupplierPromotion

    supplier = factory.SubFactory(SupplierFactory)
    car = factory.SubFactory(CarFactory)
    title = factory.Sequence(lambda n: f'Promo-{n}')
    description = ''
    discount_percent = 10
    start_date = '2026-01-01'
    end_date = '2026-12-31'
