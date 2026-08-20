from django.contrib import admin
from .models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        'store_name',
        'user',
        'city',
        'status',
        'is_active',
        'is_featured',
        'commission_rate',
        'created_at',
    ]
    list_filter = ['status', 'is_active', 'is_featured', 'city']
    list_editable = ['status', 'is_active', 'is_featured', 'commission_rate']
    search_fields = ['store_name', 'user__username', 'email', 'phone', 'city']
    prepopulated_fields = {'slug': ('store_name',)}
    readonly_fields = ['created_at', 'updated_at']
