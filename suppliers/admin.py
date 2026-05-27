from django.contrib import admin

from .models import Supplier, SupplierInventory

admin.site.register(Supplier)
admin.site.register(SupplierInventory)
