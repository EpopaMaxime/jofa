from django.contrib import admin
from .models import ConsultationPhoto, SkinConsultation


class ConsultationPhotoInline(admin.TabularInline):
    model = ConsultationPhoto
    extra = 0
    readonly_fields = ['uploaded_at', 'deleted']


@admin.register(SkinConsultation)
class SkinConsultationAdmin(admin.ModelAdmin):
    list_display = [
        'public_id',
        'user',
        'status',
        'detected_skin_type',
        'analyzer_backend',
        'confidence_score',
        'created_at',
    ]
    list_filter = ['status', 'analyzer_backend', 'detected_skin_type']
    search_fields = ['public_id', 'user__username', 'primary_goals']
    readonly_fields = ['public_id', 'analysis_payload', 'analyzed_at', 'created_at', 'updated_at']
    filter_horizontal = ['concerns', 'recommended_products']
    inlines = [ConsultationPhotoInline]
