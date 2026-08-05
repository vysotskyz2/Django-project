from datetime import date, timedelta
from decimal import Decimal

import pytest
from moneyed import Money

from cars.factories import CarFactory
from dealerships.factories import (
    DealershipBestSupplierFactory,
    DealershipCarPreferenceFactory,
    DealershipFactory,
    DealershipInventoryFactory,
    PurchaseLogFactory,
    SaleRecordFactory,
)
from dealerships.models import DealershipBestSupplier, PurchaseLog, SaleRecord
from suppliers.factories import (
    SupplierFactory,
    SupplierInventoryFactory,
    SupplierPromotionFactory,
)
from suppliers.models import SupplierInventory

DEALER_URL = "/api/v1/dealerships/"
INV_URL = "/api/v1/dealership-inventory/"
PREF_URL = "/api/v1/dealership-preferences/"
SALE_URL = "/api/v1/sale-records/"
PURCH_URL = "/api/v1/purchase-logs/"
BEST_URL = "/api/v1/best-suppliers/"
STATS_URL = "/api/v1/dealerships/{}/statistics/"


def _url(base, pk):
    return f"{base}{pk}/"


@pytest.mark.django_db
class TestDealershipAPI:
    def test_list(self, auth_client):
        DealershipFactory.create_batch(2)
        resp = auth_client.get(DEALER_URL)
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 2

    def test_create_admin_only(self, auth_client, buyer_auth_client):
        data = {"name": "New", "location": "US", "balance": "50000.00"}
        assert auth_client.post(DEALER_URL, data, format="json").status_code == 201
        assert buyer_auth_client.post(DEALER_URL, data, format="json").status_code == 403

    def test_retrieve(self, auth_client):
        d = DealershipFactory()
        resp = auth_client.get(_url(DEALER_URL, d.pk))
        assert resp.status_code == 200
        assert resp.data["name"] == d.name

    def test_soft_delete(self, auth_client):
        d = DealershipFactory()
        resp = auth_client.delete(_url(DEALER_URL, d.pk))
        assert resp.status_code == 204
        d.refresh_from_db()
        assert d.is_deleted is True

    def test_statistics(self, auth_client):
        d = DealershipFactory()
        resp = auth_client.get(STATS_URL.format(d.pk))
        assert resp.status_code == 200
        assert resp.data["cars_sold"] == 0
        assert resp.data["revenue"] == "0.00"

    def test_statistics_404(self, auth_client):
        resp = auth_client.get(STATS_URL.format(99999))
        assert resp.status_code == 404


@pytest.mark.django_db
class TestDealershipInventoryAPI:
    def test_list(self, auth_client):
        DealershipInventoryFactory.create_batch(2)
        resp = auth_client.get(INV_URL)
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 2

    def test_create_admin(self, auth_client):
        d = DealershipFactory()
        c = CarFactory()
        data = {"dealership": d.pk, "car": c.pk, "quantity": 5, "price_per_unit": "20000.00"}
        resp = auth_client.post(INV_URL, data, format="json")
        assert resp.status_code == 201


@pytest.mark.django_db
class TestDealershipPreferenceAPI:
    def test_list(self, auth_client):
        DealershipCarPreferenceFactory.create_batch(2)
        resp = auth_client.get(PREF_URL)
        assert resp.status_code == 200

    def test_create_admin(self, auth_client):
        d = DealershipFactory()
        c = CarFactory()
        data = {"dealership": d.pk, "car": c.pk, "min_stock": 3, "target_stock": 8}
        resp = auth_client.post(PREF_URL, data, format="json")
        assert resp.status_code == 201


@pytest.mark.django_db
class TestSaleRecordAPI:
    def test_list(self, auth_client):
        SaleRecordFactory.create_batch(2)
        resp = auth_client.get(SALE_URL)
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 2

    def test_create_not_allowed(self, auth_client):
        resp = auth_client.post(SALE_URL, {}, format="json")
        assert resp.status_code == 405


@pytest.mark.django_db
class TestPurchaseLogAPI:
    def test_list_admin_only(self, auth_client, buyer_auth_client):
        PurchaseLogFactory()
        assert auth_client.get(PURCH_URL).status_code == 200
        assert buyer_auth_client.get(PURCH_URL).status_code == 403


@pytest.mark.django_db
class TestBestSupplierAPI:
    def test_list(self, auth_client):
        DealershipBestSupplierFactory()
        resp = auth_client.get(BEST_URL)
        assert resp.status_code == 200


@pytest.mark.django_db
class TestDemandService:
    def test_daily_demand_with_sales(self):
        from dealerships.services import DemandService

        dealership = DealershipFactory()
        car = CarFactory()
        SaleRecord.objects.create(dealership=dealership, car=car, quantity_sold=30)

        demand = DemandService().calculate_daily_demand(dealership, car, n_days=10)
        assert demand == 3.0

    def test_daily_demand_no_sales(self):
        from dealerships.services import DemandService

        dealership = DealershipFactory()
        car = CarFactory()
        demand = DemandService().calculate_daily_demand(dealership, car, n_days=30)
        assert demand == 0.0

    def test_days_of_stock(self):
        from dealerships.services import DemandService

        dealership = DealershipFactory()
        car = CarFactory()
        DealershipInventoryFactory(dealership=dealership, car=car, quantity=20)
        SaleRecord.objects.create(dealership=dealership, car=car, quantity_sold=30)

        days = DemandService().days_of_stock(dealership, car, n_days=30)
        assert days == 20.0

    def test_days_of_stock_zero_demand(self):
        from dealerships.services import DemandService

        dealership = DealershipFactory()
        car = CarFactory()
        DealershipInventoryFactory(dealership=dealership, car=car, quantity=10)
        days = DemandService().days_of_stock(dealership, car, n_days=30)
        assert days == float("inf")


@pytest.mark.django_db
class TestPurchaseService:
    def test_successful_purchase(self):
        from dealerships.services import PurchaseService

        dealership = DealershipFactory(balance=Money(500_000, "USD"))
        supplier = SupplierFactory(balance=Money(100_000, "USD"))
        car = CarFactory()
        SupplierInventoryFactory(
            supplier=supplier, car=car, quantity=30, price_per_unit=Money(15000, "USD")
        )

        svc = PurchaseService()
        log = svc.execute_purchase(
            dealership=dealership,
            supplier=supplier,
            car=car,
            quantity=5,
            price_per_unit=Decimal("14000.00"),
            reason="test purchase",
        )

        assert log.purchased is True
        assert log.quantity == 5
        dealership.refresh_from_db()
        supplier.refresh_from_db()
        assert dealership.balance.amount == Decimal("430000.00")
        assert supplier.balance.amount == Decimal("170000.00")

        from dealerships.models import DealershipInventory

        inv = DealershipInventory.objects.get(dealership=dealership, car=car)
        assert inv.quantity == 5

    def test_insufficient_dealership_balance(self):
        from dealerships.services import PurchaseService

        dealership = DealershipFactory(balance=Money(1_000, "USD"))
        supplier = SupplierFactory()
        car = CarFactory()
        SupplierInventoryFactory(supplier=supplier, car=car, quantity=30)

        svc = PurchaseService()
        with pytest.raises(ValueError, match="Insufficient balance"):
            svc.execute_purchase(
                dealership=dealership,
                supplier=supplier,
                car=car,
                quantity=5,
                price_per_unit=Decimal("14000.00"),
                reason="test",
            )

    def test_insufficient_supplier_stock(self):
        from dealerships.services import PurchaseService

        dealership = DealershipFactory(balance=Money(500_000, "USD"))
        supplier = SupplierFactory()
        car = CarFactory()
        SupplierInventoryFactory(supplier=supplier, car=car, quantity=2)

        svc = PurchaseService()
        with pytest.raises(ValueError, match="Insufficient stock"):
            svc.execute_purchase(
                dealership=dealership,
                supplier=supplier,
                car=car,
                quantity=5,
                price_per_unit=Decimal("1000.00"),
                reason="test",
            )


@pytest.mark.django_db
class TestProcurementService:
    def test_preferred_car_replenished(self):
        from dealerships.services import ProcurementService

        dealership = DealershipFactory(balance=Money(500_000, "USD"))
        supplier = SupplierFactory()
        car = CarFactory()
        SupplierInventoryFactory(
            supplier=supplier, car=car, quantity=50, price_per_unit=Money(10000, "USD")
        )
        DealershipCarPreferenceFactory(
            dealership=dealership,
            car=car,
            min_stock=5,
            target_stock=15,
        )

        ProcurementService().run_for_dealership(dealership.pk, n_days=30)

        from dealerships.models import DealershipInventory

        inv = DealershipInventory.objects.get(dealership=dealership, car=car)
        assert inv.quantity == 15

        logs = PurchaseLog.objects.filter(dealership=dealership, car=car, purchased=True)
        assert logs.count() == 1

    def test_skip_sufficient_stock(self):
        from dealerships.services import ProcurementService

        dealership = DealershipFactory(balance=Money(500_000, "USD"))
        car = CarFactory()
        DealershipInventoryFactory(dealership=dealership, car=car, quantity=20)
        DealershipCarPreferenceFactory(
            dealership=dealership,
            car=car,
            min_stock=5,
            target_stock=15,
        )

        ProcurementService().run_for_dealership(dealership.pk, n_days=30)

        skip_logs = PurchaseLog.objects.filter(dealership=dealership, car=car, purchased=False)
        assert skip_logs.count() == 1
        assert "sufficient stock" in skip_logs.first().reason

    def test_skip_no_supplier(self):
        from dealerships.services import ProcurementService

        dealership = DealershipFactory(balance=Money(500_000, "USD"))
        car = CarFactory()
        DealershipCarPreferenceFactory(
            dealership=dealership,
            car=car,
            min_stock=10,
            target_stock=20,
        )

        ProcurementService().run_for_dealership(dealership.pk, n_days=30)

        skip_logs = PurchaseLog.objects.filter(dealership=dealership, car=car, purchased=False)
        assert skip_logs.count() >= 1
        assert any("no supplier" in log.reason.lower() for log in skip_logs)

    def test_deleted_dealership_skipped(self):
        from dealerships.services import ProcurementService

        dealership = DealershipFactory(is_deleted=True)

        ProcurementService().run_for_dealership(dealership.pk, n_days=30)
        assert PurchaseLog.objects.filter(dealership=dealership).count() == 0


@pytest.mark.django_db
class TestSupplierRankingService:
    def test_computes_effective_price(self):
        from dealerships.services import SupplierPriceService, SupplierRankingService

        dealership = DealershipFactory()
        supplier = SupplierFactory()
        car = CarFactory()
        SupplierInventoryFactory(
            supplier=supplier, car=car, quantity=20, price_per_unit=Money(12000, "USD")
        )
        SupplierPromotionFactory(
            supplier=supplier,
            car=car,
            discount_percent=10,
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=1),
        )

        inv = SupplierInventory.objects.get(supplier=supplier, car=car)
        effective = SupplierPriceService().get_effective_price(inv)
        assert effective == Decimal("10800.00")

        SupplierRankingService().run_for_dealership(dealership.pk)

        best = DealershipBestSupplier.objects.filter(dealership=dealership, car=car).first()
        assert best is not None
        assert best.supplier == supplier
        assert best.effective_price.amount == Decimal("10800.00")

    def test_no_supplier_creates_null_entry(self):
        from dealerships.services import SupplierRankingService

        dealership = DealershipFactory()
        SupplierRankingService().run_for_dealership(dealership.pk)

    def test_picks_best_supplier(self):
        from dealerships.services import SupplierRankingService

        dealership = DealershipFactory()
        car = CarFactory()
        cheap = SupplierFactory(name="CheapCo")
        expensive = SupplierFactory(name="ExpInc")
        SupplierInventoryFactory(
            supplier=cheap, car=car, quantity=10, price_per_unit=Money(10000, "USD")
        )
        SupplierInventoryFactory(
            supplier=expensive, car=car, quantity=10, price_per_unit=Money(20000, "USD")
        )

        SupplierRankingService().run_for_dealership(dealership.pk)

        best = DealershipBestSupplier.objects.get(dealership=dealership, car=car)
        assert best.supplier == cheap


@pytest.mark.django_db
class TestProcurementViaCeleryTask:
    def test_process_dealership_procurement_full_flow(self):
        from dealerships.tasks import process_dealership_procurement

        dealership = DealershipFactory(balance=Money(500_000, "USD"))
        supplier = SupplierFactory()
        car = CarFactory()
        SupplierInventoryFactory(
            supplier=supplier, car=car, quantity=30, price_per_unit=Money(10000, "USD")
        )
        DealershipCarPreferenceFactory(
            dealership=dealership,
            car=car,
            min_stock=5,
            target_stock=10,
        )

        process_dealership_procurement(dealership.pk, n_days=30)

        from dealerships.models import DealershipInventory

        inv = DealershipInventory.objects.get(dealership=dealership, car=car)
        assert inv.quantity == 10
        assert PurchaseLog.objects.filter(dealership=dealership, purchased=True).exists()


@pytest.mark.django_db
class TestSupplierRankingViaCeleryTask:
    def test_process_supplier_ranking_updates_best_supplier(self):
        from dealerships.tasks import process_dealership_supplier_ranking

        dealership = DealershipFactory()
        supplier = SupplierFactory()
        car = CarFactory()
        SupplierInventoryFactory(
            supplier=supplier, car=car, quantity=10, price_per_unit=Money(8000, "USD")
        )

        process_dealership_supplier_ranking(dealership.pk)

        best = DealershipBestSupplier.objects.filter(dealership=dealership, car=car).first()
        assert best is not None
        assert best.supplier == supplier
