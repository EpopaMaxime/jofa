from django.contrib import admin
from .models import IntegrationProvider, PaymentTransaction, Shipment


@admin.register(IntegrationProvider)
class IntegrationProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'is_active', 'is_default']
    list_filter = ['category', 'is_active', 'is_default']
    list_editable = ['is_active', 'is_default']
    search_fields = ['name', 'slug', 'notes']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'provider_slug',
        'amount',
        'currency',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'provider_slug']
    search_fields = ['external_id', 'order__id', 'order__email']
    readonly_fields = ['raw_response', 'created_at', 'updated_at', 'paid_at']


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'tracking_number',
        'provider_slug',
        'status',
        'estimated_delivery',
    ]
    list_filter = ['status', 'provider_slug']
    list_editable = ['status']
    search_fields = ['tracking_number', 'order__id']
    actions = ['mark_delivered']

    @admin.action(description='Mark selected shipments as delivered (collects COD)')
    def mark_delivered(self, request, queryset):
        updated = 0
        for shipment in queryset:
            shipment.status = 'delivered'
            shipment.save()
            updated += 1
        self.message_user(request, f'{updated} shipment(s) marked delivered.')
