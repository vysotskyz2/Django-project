from django.contrib import admin

from .models import Supplier, SupplierInventory, SupplierPromotion

admin.site.register(Supplier)
admin.site.register(SupplierInventory)
admin.site.register(SupplierPromotion)
