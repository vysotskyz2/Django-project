import factory
import factory.django

from cars.models import Brand, Car, Color, FuelType, Transmission


class CarFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Car

    brand = Brand.TOYOTA
    model_name = factory.Sequence(lambda n: f"Model-{n}")
    year = 2024
    color = Color.BLACK
    transmission = Transmission.AUTOMATIC
    fuel_type = FuelType.PETROL
