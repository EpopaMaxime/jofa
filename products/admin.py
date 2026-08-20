from django.contrib import admin
from .models import Category, Product, Coupon, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'category', 'price', 'discount_percentage', 'stock', 'available', 'featured', 'created_at']
    list_filter = ['available', 'featured', 'created_at', 'category', 'skin_type', 'vendor']
    list_editable = ['price', 'discount_percentage', 'stock', 'available', 'featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'ingredients', 'vendor__store_name']
    autocomplete_fields = ['vendor', 'category']
    inlines = [ProductImageInline]

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'valid_from', 'valid_to', 'active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']
    filter_horizontal = ['products']
