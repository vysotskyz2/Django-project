from django.contrib import admin

from dealerships.models import (
    Dealership,
    DealershipCarPreference,
    DealershipInventory,
    PurchaseLog,
    SaleRecord,
)

admin.site.register(Dealership)
admin.site.register(DealershipInventory)
admin.site.register(DealershipCarPreference)
admin.site.register(SaleRecord)
admin.site.register(PurchaseLog)
