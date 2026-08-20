from django.contrib import admin
from .models import ConcernProductMap, RoutineBundle, RoutineStep, SkinConcern


class ConcernProductMapInline(admin.TabularInline):
    model = ConcernProductMap
    extra = 1
    autocomplete_fields = ['product']


class RoutineStepInline(admin.TabularInline):
    model = RoutineStep
    extra = 1
    autocomplete_fields = ['product']


@admin.register(SkinConcern)
class SkinConcernAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'severity_weight', 'is_active']
    list_editable = ['severity_weight', 'is_active']
    search_fields = ['name', 'code', 'keywords']
    prepopulated_fields = {'code': ('name',)}
    inlines = [ConcernProductMapInline]


@admin.register(ConcernProductMap)
class ConcernProductMapAdmin(admin.ModelAdmin):
    list_display = ['concern', 'product', 'role', 'priority', 'is_active']
    list_filter = ['concern', 'role', 'is_active']
    list_editable = ['priority', 'is_active', 'role']
    search_fields = ['product__name', 'concern__name', 'notes']
    autocomplete_fields = ['product', 'concern']


@admin.register(RoutineBundle)
class RoutineBundleAdmin(admin.ModelAdmin):
    list_display = ['name', 'skin_type', 'featured', 'is_active']
    list_editable = ['featured', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['concerns']
    inlines = [RoutineStepInline]
