from django.core.validators import MaxValueValidator, MinValueValidator
from django_countries.fields import CountryField
from djmoney.models.fields import MoneyField
from django.db import models

from cars.models import Car
from core.mixins import CreatedAtMixin, IsDeletedMixin, UpdatedAtMixin


class Supplier(CreatedAtMixin, UpdatedAtMixin, IsDeletedMixin):
    name = models.CharField(max_length=200)
    country = CountryField()
    balance = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'

    def __str__(self):
        return self.name


class SupplierInventory(CreatedAtMixin, UpdatedAtMixin):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='inventory'
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name='supplier_inventory'
    )
    quantity = models.PositiveIntegerField(default=0)
    price_per_unit = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')

    class Meta:
        verbose_name = 'Supplier Inventory'
        verbose_name_plural = 'Supplier Inventories'
        unique_together = ('supplier', 'car')

    def __str__(self):
        return f'{self.supplier.name} — {self.car} × {self.quantity}'


class SupplierPromotion(CreatedAtMixin, UpdatedAtMixin):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='promotions'
    )
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='supplier_promotions',
        help_text='Leave blank to apply this promotion to all cars from this supplier.',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Discount percentage (0–100).',
    )
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = 'Supplier Promotion'
        verbose_name_plural = 'Supplier Promotions'

    def __str__(self):
        car_label = str(self.car) if self.car else 'all cars'
        return f'{self.supplier.name} — {self.title} ({self.discount_percent}% off {car_label})'
