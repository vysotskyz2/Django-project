import factory
import factory.django

from promotions.models import Promotion, PromotionType


class PromotionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Promotion

    dealership = factory.SubFactory("dealerships.factories.DealershipFactory")
    title = factory.Sequence(lambda n: f"Promotion-{n}")
    description = ""
    type = PromotionType.SEASONAL
    discount_percent = 15
    start_date = "2026-01-01"
    end_date = "2026-12-31"
