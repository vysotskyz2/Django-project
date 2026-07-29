from decimal import Decimal
from django.db.models import QuerySet, Sum, Count
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
from moneyed import Money
from dealerships.models import (
    Dealership,
    DealershipBestSupplier,
    DealershipCarPreference,
    DealershipInventory,
    PurchaseLog,
    SaleRecord,
)

class DealershipRepository:
    def get_active_ids(self) -> list[int]:
        return list(
            Dealership.objects.filter(is_deleted=False).values_list('id', flat=True)
        )

    def get_active_by_id(self, dealership_id: int) -> Dealership | None:
        try:
            return Dealership.objects.get(pk=dealership_id, is_deleted=False)
        except Dealership.DoesNotExist:
            return None

    def get_active_or_404(self, dealership_id: int) -> Dealership:
        return Dealership.objects.get(pk=dealership_id, is_deleted=False)

    def lock_for_update(self, dealership_id: int) -> Dealership:
        return Dealership.objects.select_for_update().get(pk=dealership_id)

    def deduct_balance(self, dealership: Dealership, amount: Money) -> None:
        dealership.balance -= amount
        dealership.save(update_fields=['balance', 'balance_currency'])

    def add_balance(self, dealership: Dealership, amount: Money) -> None:
        dealership.balance += amount
        dealership.save(update_fields=['balance', 'balance_currency'])


class DealershipInventoryRepository:
    def get_current_stock(self, dealership: Dealership, car) -> int:
        try:
            return DealershipInventory.objects.get(
                dealership=dealership, car=car
            ).quantity
        except DealershipInventory.DoesNotExist:
            return 0

    def get_all_for_dealership(self, dealership: Dealership) -> QuerySet:
        return (
            DealershipInventory.objects
            .filter(dealership=dealership)
            .select_related('car')
        )

    def get_or_create(
        self,
        dealership: Dealership,
        car,
        default_price: Money,
    ) -> DealershipInventory:
        inv, _ = DealershipInventory.objects.get_or_create(
            dealership=dealership,
            car=car,
            defaults={'quantity': 0, 'price_per_unit': default_price},
        )
        return inv

    def add_stock(self, inventory: DealershipInventory, quantity: int) -> None:
        inventory.quantity += quantity
        inventory.save(update_fields=['quantity'])

    def find_matching_for_car(self, car, price_limit: Decimal) -> list[DealershipInventory]:
        return list(
            DealershipInventory.objects
            .select_related('dealership', 'car')
            .filter(
                car=car,
                quantity__gte=1,
                price_per_unit__lte=price_limit,
                dealership__is_deleted=False,
            )
        )

    def lock_for_dealership_and_car(self, dealership, car) -> DealershipInventory:
        return (
            DealershipInventory.objects
            .select_for_update()
            .get(dealership=dealership, car=car)
        )

    def deduct_stock(self, inventory: DealershipInventory, quantity: int) -> None:
        inventory.quantity -= quantity
        inventory.save(update_fields=['quantity'])

    def get_total_units(self, dealership: Dealership) -> int:
        result = DealershipInventory.objects.filter(dealership=dealership).aggregate(
            total=Sum('quantity'),
        )
        return result['total'] or 0


class DealershipCarPreferenceRepository:
    def get_preferred_for_dealership(
        self, dealership: Dealership
    ) -> QuerySet[DealershipCarPreference]:
        return (
            DealershipCarPreference.objects
            .filter(dealership=dealership, is_preferred=True)
            .select_related('car')
        )

    def get_by_dealership_and_car(
        self, dealership: Dealership, car
    ) -> DealershipCarPreference | None:
        return DealershipCarPreference.objects.filter(
            dealership=dealership, car=car
        ).first()

class SaleRecordRepository:
    def create(self, dealership: Dealership, car, quantity_sold: int) -> SaleRecord:
        return SaleRecord.objects.create(
            dealership=dealership,
            car=car,
            quantity_sold=quantity_sold,
        )

    def get_total_sold(
        self,
        dealership: Dealership,
        car,
        n_days: int,
    ) -> int:
        since = timezone.now() - timedelta(days=n_days)
        result = SaleRecord.objects.filter(
            dealership=dealership,
            car=car,
            sold_at__gte=since,
        ).aggregate(total=Sum('quantity_sold'))
        return result['total'] or 0

    def get_total_sold_all_cars(self, dealership: Dealership) -> int:
        result = SaleRecord.objects.filter(dealership=dealership).aggregate(
            total=Sum('quantity_sold'),
        )
        return result['total'] or 0

class PurchaseLogRepository:
    def log_purchase(
        self,
        *,
        dealership: Dealership,
        supplier,
        car,
        quantity: int,
        price_per_unit: Money,
        total_cost: Money,
        reason: str,
    ) -> PurchaseLog:
        return PurchaseLog.objects.create(
            dealership=dealership,
            supplier=supplier,
            car=car,
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_cost=total_cost,
            purchased=True,
            reason=reason,
        )

    def get_total_spend(self, dealership: Dealership) -> Decimal:
        total = PurchaseLog.objects.filter(
            dealership=dealership, purchased=True,
        ).aggregate(total=Sum('total_cost'))['total']
        if total is None:
            return Decimal('0.00')
        if hasattr(total, 'amount'):
            return total.amount
        return Decimal(str(total))

    def get_stats_for_supplier(self, supplier) -> dict:
        purchased = PurchaseLog.objects.filter(supplier=supplier, purchased=True)
        deals_count = purchased.count()
        cars_sold = purchased.aggregate(total=Sum('quantity'))['total'] or 0
        income = purchased.aggregate(total=Sum('total_cost'))['total']
        if income is None:
            income = Decimal('0.00')
        elif hasattr(income, 'amount'):
            income = income.amount
        else:
            income = Decimal(str(income))
        partner_rows = list(
            purchased.exclude(dealership__isnull=True)
            .values('dealership_id', 'dealership__name')
            .annotate(deals=Count('id'), units=Sum('quantity'))
            .order_by('dealership__name')
        )
        return {
            'deals_count': deals_count,
            'cars_sold': cars_sold,
            'income': income,
            'partner_rows': partner_rows,
        }

    def log_skip(
        self,
        *,
        dealership: Dealership,
        car,
        reason: str,
        supplier=None,
    ) -> PurchaseLog:
        return PurchaseLog.objects.create(
            dealership=dealership,
            supplier=supplier,
            car=car,
            quantity=0,
            purchased=False,
            reason=reason,
        )

class DealershipBestSupplierRepository:
    def get_by_dealership_and_car(
        self, dealership: Dealership, car
    ) -> DealershipBestSupplier | None:
        return DealershipBestSupplier.objects.filter(
            dealership=dealership, car=car
        ).select_related('supplier').first()

    def get_all_for_dealership(self, dealership: Dealership) -> QuerySet:
        return (
            DealershipBestSupplier.objects
            .filter(dealership=dealership)
            .select_related('supplier', 'car')
        )

    def upsert(
        self,
        *,
        dealership: Dealership,
        car,
        supplier,
        effective_price: Money | None,
        reason: str,
    ) -> tuple[DealershipBestSupplier, bool]:
        with transaction.atomic():
            existing = (
                DealershipBestSupplier.objects
                .select_for_update()
                .filter(dealership=dealership, car=car)
                .first()
            )

            if existing is None:
                try:
                    with transaction.atomic():
                        obj = DealershipBestSupplier.objects.create(
                            dealership=dealership,
                            car=car,
                            supplier=supplier,
                            effective_price=effective_price,
                            reason=reason,
                        )
                        return obj, True
                except IntegrityError:
                    existing = (
                        DealershipBestSupplier.objects
                        .select_for_update()
                        .filter(dealership=dealership, car=car)
                        .first()
                    )

            existing = (
                DealershipBestSupplier.objects
                .select_related('supplier')
                .get(pk=existing.pk)
            )

            old_supplier_id = existing.supplier_id
            old_price = existing.effective_price.amount if existing.effective_price else None
            new_price = effective_price.amount if effective_price else None

            changed = (
                (old_supplier_id != getattr(supplier, 'pk', None))
                or (old_price != new_price)
            )

            existing.supplier = supplier
            existing.effective_price = effective_price
            existing.reason = reason
            existing.save(
                update_fields=[
                    'supplier', 'effective_price', 'effective_price_currency',
                    'reason', 'updated_at',
                ]
            )

            return existing, changed
