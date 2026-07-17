from django.contrib.auth.models import User
from django.db import models
from djmoney.models.fields import MoneyField
from cars.models import Car
from core.mixins import CreatedAtMixin, IsDeletedMixin, UpdatedAtMixin


class Buyer(CreatedAtMixin, UpdatedAtMixin, IsDeletedMixin):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='buyer_profile',
    )
    balance = MoneyField(
        max_digits=14, decimal_places=2, default_currency='USD',
        help_text='Available funds for purchasing cars.',
    )

    class Meta:
        verbose_name = 'Buyer'
        verbose_name_plural = 'Buyers'

    @property
    def is_email_verified(self) -> bool:
        return self.user.is_active

    def __str__(self) -> str:
        return f'Buyer({self.user.username}) - {self.balance}'


class BuyerCarPreference(CreatedAtMixin, UpdatedAtMixin):
    buyer = models.ForeignKey(
        Buyer,
        on_delete=models.CASCADE,
        related_name='car_preferences',
    )
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='buyer_preferences',
    )
    max_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency='USD',
        help_text='Maximum price the buyer is willing to pay for this car model.',
    )

    class Meta:
        verbose_name = 'Buyer Car Preference'
        verbose_name_plural = 'Buyer Car Preferences'
        unique_together = ('buyer', 'car')

    def __str__(self) -> str:
        return f'{self.buyer.user.username} - {self.car} (max {self.max_price})'
