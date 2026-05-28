from django_countries.fields import CountryField
from djmoney.models.fields import MoneyField
from django.db import models

from cars.models import Car
from core.mixins import CreatedAtMixin, IsDeletedMixin, UpdatedAtMixin


class Dealership(CreatedAtMixin, UpdatedAtMixin, IsDeletedMixin):
    name = models.CharField(max_length=200)
    location = CountryField()
    balance = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')

    class Meta:
        verbose_name = 'Dealership'
        verbose_name_plural = 'Dealerships'

    def __str__(self):
        return self.name


class DealershipInventory(CreatedAtMixin, UpdatedAtMixin):
    dealership = models.ForeignKey(
        Dealership, on_delete=models.CASCADE, related_name='inventory'
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name='dealership_inventory'
    )
    quantity = models.PositiveIntegerField(default=0)
    price_per_unit = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')

    class Meta:
        verbose_name = 'Dealership Inventory'
        verbose_name_plural = 'Dealership Inventories'
        unique_together = ('dealership', 'car')

    def __str__(self):
        return f'{self.dealership.name} — {self.car} × {self.quantity}'
