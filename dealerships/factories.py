import factory
import factory.django
from django.contrib.auth.models import User
from moneyed import Money

from cars.factories import CarFactory
from dealerships.models import (
    Dealership,
    DealershipBestSupplier,
    DealershipCarPreference,
    DealershipInventory,
    PurchaseLog,
    SaleRecord,
)
from suppliers.factories import SupplierFactory


class DealershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dealership

    name = factory.Sequence(lambda n: f"Dealership-{n}")
    location = "US"
    balance = Money(100_000, "USD")


class DealershipInventoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DealershipInventory

    dealership = factory.SubFactory(DealershipFactory)
    car = factory.SubFactory(CarFactory)
    quantity = 10
    price_per_unit = Money(20_000, "USD")


class DealershipCarPreferenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DealershipCarPreference

    dealership = factory.SubFactory(DealershipFactory)
    car = factory.SubFactory(CarFactory)
    min_stock = 5
    target_stock = 15
    is_preferred = True


class SaleRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SaleRecord

    dealership = factory.SubFactory(DealershipFactory)
    car = factory.SubFactory(CarFactory)
    quantity_sold = 1


class PurchaseLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PurchaseLog

    dealership = factory.SubFactory(DealershipFactory)
    supplier = factory.SubFactory(SupplierFactory)
    car = factory.SubFactory(CarFactory)
    quantity = 5
    price_per_unit = Money(15_000, "USD")
    total_cost = Money(75_000, "USD")
    purchased = True
    reason = "stock replenishment"


class DealershipBestSupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DealershipBestSupplier

    dealership = factory.SubFactory(DealershipFactory)
    car = factory.SubFactory(CarFactory)
    supplier = factory.SubFactory(SupplierFactory)
    effective_price = Money(18_000, "USD")
    reason = "best price"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
