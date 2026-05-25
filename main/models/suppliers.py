from django.db import models
from models.basemodel import BaseModel
from models.cars import Car
from django_countries.fields import CountryField
from djmoney.models.fields import MoneyField

class Supplier(BaseModel):
    name = models.CharField(max_length=200)
    country = CountryField()
    balance = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'

    def __str__(self):
        return self.name


class SupplierInventory(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='inventory'
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name='supplier_inventory'
    )
    quantity = models.PositiveIntegerField(default=0)
    price_per_unit = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Supplier Inventory'
        verbose_name_plural = 'Supplier Inventories'
        unique_together = ('supplier', 'car')

    def __str__(self):
        return f'{self.supplier.name} — {self.car} × {self.quantity}'