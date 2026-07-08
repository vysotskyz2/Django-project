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


class DealershipCarPreference(CreatedAtMixin, UpdatedAtMixin):
    dealership = models.ForeignKey(
        Dealership, on_delete=models.CASCADE, related_name='car_preferences'
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name='dealership_preferences'
    )
    min_stock = models.PositiveIntegerField(
        default=5,
        help_text='Minimum stock level. Reorder is triggered when stock falls below this.',
    )
    target_stock = models.PositiveIntegerField(
        default=10,
        help_text='Target stock level after reorder.',
    )
    is_preferred = models.BooleanField(
        default=True,
        help_text='If True, this car is always checked in procurement Pass 1.',
    )

    class Meta:
        verbose_name = 'Dealership Car Preference'
        verbose_name_plural = 'Dealership Car Preferences'
        unique_together = ('dealership', 'car')

    def __str__(self):
        return (
            f'{self.dealership.name} — {self.car} '
            f'(min={self.min_stock}, target={self.target_stock})'
        )


class SaleRecord(CreatedAtMixin):
    dealership = models.ForeignKey(
        Dealership, on_delete=models.CASCADE, related_name='sale_records'
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name='sale_records'
    )
    quantity_sold = models.PositiveIntegerField()
    sold_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sale Record'
        verbose_name_plural = 'Sale Records'
        indexes = [
            models.Index(fields=['dealership', 'car', 'sold_at']),
        ]

    def __str__(self):
        return f'{self.dealership.name} — {self.car} × {self.quantity_sold}'


class PurchaseLog(models.Model):
    dealership = models.ForeignKey(
        Dealership, on_delete=models.CASCADE, related_name='purchase_logs'
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_logs',
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name='purchase_logs'
    )
    quantity = models.PositiveIntegerField(default=0)
    price_per_unit = MoneyField(
        max_digits=14, decimal_places=2, default_currency='USD',
        null=True, blank=True,
    )
    total_cost = MoneyField(
        max_digits=14, decimal_places=2, default_currency='USD',
        null=True, blank=True,
    )
    purchased = models.BooleanField(
        help_text='True = purchase was made; False = skipped.',
    )
    reason = models.TextField(
        help_text='Reason for purchase or skip (stock level, price, balance, etc.).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Purchase Log'
        verbose_name_plural = 'Purchase Logs'
        indexes = [
            models.Index(fields=['dealership', 'created_at']),
            models.Index(fields=['purchased']),
        ]

    def __str__(self):
        status = 'BOUGHT' if self.purchased else 'SKIPPED'
        return f'[{status}] {self.dealership.name} — {self.car} × {self.quantity}'
