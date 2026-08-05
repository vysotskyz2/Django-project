from django.db import models
from djmoney.models.fields import MoneyField

from cars.models import Car
from core.mixins import CreatedAtMixin, IsDeletedMixin, UpdatedAtMixin
from dealerships.models import Dealership
from suppliers.models import Supplier


class OfferStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    CANCELLED = "cancelled", "Cancelled"


class Offer(CreatedAtMixin, UpdatedAtMixin, IsDeletedMixin):
    buyer = models.ForeignKey(
        "buyers.Buyer",
        on_delete=models.CASCADE,
        related_name="offers",
        null=True,
        blank=True,
    )
    dealership = models.ForeignKey(
        Dealership,
        on_delete=models.CASCADE,
        related_name="offers",
        null=True,
        blank=True,
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="offers",
        null=True,
        blank=True,
    )
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="offers")
    quantity = models.PositiveIntegerField(default=1)
    offered_price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        null=True,
        blank=True,
        help_text="Actual agreed price per unit. Null until the deal is executed.",
    )
    max_budget = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
        help_text="Maximum price the requester is willing to pay per unit.",
    )
    status = models.CharField(
        max_length=20,
        choices=OfferStatus.choices,
        default=OfferStatus.PENDING,
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for acceptance or rejection.",
    )

    class Meta:
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        indexes = [
            models.Index(fields=["buyer", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        if self.buyer_id:
            return (
                f"BuyerOffer #{self.pk}: {self.buyer} → {self.dealership or 'TBD'} "
                f"({self.car}, {self.get_status_display()})"
            )
        return (
            f"Offer #{self.pk}: {self.dealership} - {self.supplier} "
            f"({self.car}, {self.get_status_display()})"
        )
