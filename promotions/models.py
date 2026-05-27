from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from dealerships.models import Dealership
from core.mixins import CreatedAtMixin, UpdatedAtMixin


class PromotionType(models.TextChoices):
    SEASONAL = 'seasonal', 'Seasonal'
    CLEARANCE = 'clearance', 'Clearance'
    LOYALTY = 'loyalty', 'Loyalty'
    REFERRAL = 'referral', 'Referral'
    HOLIDAY = 'holiday', 'Holiday'


class Promotion(CreatedAtMixin, UpdatedAtMixin):
    dealership = models.ForeignKey(
        Dealership, on_delete=models.CASCADE, related_name='promotions'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=PromotionType.choices)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = 'Promotion'
        verbose_name_plural = 'Promotions'

    def __str__(self):
        return f'{self.title} ({self.get_type_display()})'
