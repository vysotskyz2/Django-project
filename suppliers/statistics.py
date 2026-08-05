from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound

from dealerships.repositories import PurchaseLogRepository
from suppliers.repositories import SupplierRepository


class SupplierStatisticsService:
    def __init__(self) -> None:
        self._supplier_repo = SupplierRepository()
        self._purchase_repo = PurchaseLogRepository()

    def get_statistics(self, supplier_id: int) -> dict:
        try:
            supplier = self._supplier_repo.get_active_or_404(supplier_id)
        except ObjectDoesNotExist:
            raise NotFound(detail="Supplier not found.") from None

        stats = self._purchase_repo.get_stats_for_supplier(supplier)

        partner_dealerships = [
            {
                "dealership_id": row["dealership_id"],
                "dealership_name": row["dealership__name"],
                "deals": row["deals"],
                "units": row["units"],
            }
            for row in stats["partner_rows"]
        ]

        return {
            "supplier_id": supplier.pk,
            "supplier_name": supplier.name,
            "deals_count": stats["deals_count"],
            "cars_sold": stats["cars_sold"],
            "income": stats["income"],
            "income_currency": "USD",
            "partner_dealerships_count": len(partner_dealerships),
            "partner_dealerships": partner_dealerships,
            "balance": supplier.balance.amount,
            "balance_currency": str(supplier.balance.currency),
        }
