from promotions.models import Promotion


class PromotionRepository:
    def get_active_dealership_ids(
        self,
        dealership_ids: list[int],
        reference_date,
    ) -> set[int]:
        return set(
            Promotion.objects.filter(
                dealership_id__in=dealership_ids,
                start_date__lte=reference_date,
                end_date__gte=reference_date,
            )
            .values_list("dealership_id", flat=True)
            .distinct()
        )
