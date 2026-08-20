from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'approved', 'created_at']
    list_filter = ['approved', 'rating', 'created_at']
    list_editable = ['approved']
    search_fields = ['user__username', 'product__name', 'comment']
