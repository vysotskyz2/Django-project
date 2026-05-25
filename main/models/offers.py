from django.db import models
from models.basemodel import BaseModel
from models.dealerships import Dealership
from models.cars import Car
from models.suppliers import Supplier
from djmoney.models.fields import MoneyField



class OfferStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'
    CANCELLED = 'cancelled', 'Cancelled'



class Offer(BaseModel):
    dealership = models.ForeignKey(
        Dealership, on_delete=models.CASCADE, related_name='offers'
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='offers'
    )
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='offers')
    quantity = models.PositiveIntegerField(default=1)
    offered_price = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')
    max_budget = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')
    status = models.CharField(
        max_length=20, choices=OfferStatus.choices, default=OfferStatus.PENDING
    )

    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'

    def __str__(self):
        return (
            f'Offer #{self.pk}: {self.dealership} → {self.supplier} '
            f'({self.car}, {self.get_status_display()})'
        )