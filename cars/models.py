from datetime import datetime

from django.core.validators import MaxValueValidator
from django.db import models

from core.mixins import CreatedAtMixin, IsDeletedMixin, UpdatedAtMixin


class Brand(models.TextChoices):
    TOYOTA = "toyota", "Toyota"
    BMW = "bmw", "BMW"
    MERCEDES = "mercedes", "Mercedes-Benz"
    AUDI = "audi", "Audi"
    FORD = "ford", "Ford"
    HONDA = "honda", "Honda"
    HYUNDAI = "hyundai", "Hyundai"
    KIA = "kia", "Kia"
    VOLKSWAGEN = "volkswagen", "Volkswagen"
    NISSAN = "nissan", "Nissan"


class Color(models.TextChoices):
    WHITE = "white", "White"
    BLACK = "black", "Black"
    SILVER = "silver", "Silver"
    RED = "red", "Red"
    BLUE = "blue", "Blue"
    GRAY = "gray", "Gray"
    GREEN = "green", "Green"


class Transmission(models.TextChoices):
    AUTOMATIC = "automatic", "Automatic"
    MANUAL = "manual", "Manual"
    CVT = "cvt", "CVT"
    SEMI_AUTOMATIC = "semi_automatic", "Semi-Automatic"


class FuelType(models.TextChoices):
    PETROL = "petrol", "Petrol"
    DIESEL = "diesel", "Diesel"
    ELECTRIC = "electric", "Electric"
    HYBRID = "hybrid", "Hybrid"
    LPG = "lpg", "LPG"


class Car(CreatedAtMixin, UpdatedAtMixin, IsDeletedMixin):
    brand = models.CharField(max_length=50, choices=Brand.choices)
    model_name = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField(validators=[MaxValueValidator(datetime.now().year)])
    color = models.CharField(max_length=50, choices=Color.choices)
    transmission = models.CharField(max_length=20, choices=Transmission.choices)
    fuel_type = models.CharField(max_length=20, choices=FuelType.choices)

    class Meta:
        verbose_name = "Car"
        verbose_name_plural = "Cars"

    def __str__(self):
        return f"{self.get_brand_display()} {self.model_name} ({self.year})"
