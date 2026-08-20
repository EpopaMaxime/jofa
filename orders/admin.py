from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'email', 'city', 'paid', 'status', 'created', 'updated']
    list_filter = ['paid', 'created', 'updated', 'status']
    list_editable = ['status', 'paid']
    inlines = [OrderItemInline]
    search_fields = ['first_name', 'last_name', 'email', 'user__username']
