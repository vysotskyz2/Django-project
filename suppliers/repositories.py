from django.db.models import Q, QuerySet
from moneyed import Money
from suppliers.models import Supplier, SupplierInventory, SupplierPromotion
from cars.models import Car

class SupplierRepository:
    def get_active_or_404(self, supplier_id: int) -> Supplier:
        return Supplier.objects.get(pk=supplier_id, is_deleted=False)

    def lock_for_update(self, supplier_id: int) -> Supplier:
        return Supplier.objects.select_for_update().get(pk=supplier_id)

    def add_balance(self, supplier: Supplier, amount: Money) -> None:
        supplier.balance += amount
        supplier.save(update_fields=['balance', 'balance_currency'])


class SupplierInventoryRepository:
    def get_available_for_car(self, car, min_quantity: int) -> QuerySet[SupplierInventory]:
        return (
            SupplierInventory.objects
            .select_related('supplier', 'car')
            .filter(
                car=car,
                quantity__gte=min_quantity,
                supplier__is_deleted=False,
            )
        )

    def get_all_cars_with_stock(self):
        car_ids = (
            SupplierInventory.objects
            .filter(quantity__gte=1, supplier__is_deleted=False)
            .values_list('car_id', flat=True)
            .distinct()
        )
        return Car.objects.filter(pk__in=car_ids)

    def lock_for_update(self, supplier: Supplier, car) -> SupplierInventory:
        return SupplierInventory.objects.select_for_update().get(
            supplier=supplier, car=car
        )

    def deduct_stock(self, inventory: SupplierInventory, quantity: int) -> None:
        inventory.quantity -= quantity
        inventory.save(update_fields=['quantity'])


class SupplierPromotionRepository:
    def get_active_for(
        self,
        supplier: Supplier,
        car,
        today,
    ) -> QuerySet[SupplierPromotion]:
        return SupplierPromotion.objects.filter(
            supplier=supplier,
            start_date__lte=today,
            end_date__gte=today,
        ).filter(
            Q(car=car) | Q(car__isnull=True)
        )
