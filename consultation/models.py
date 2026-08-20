import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from recommendations.models import SkinConcern
from products.models import Product


def consultation_upload_to(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'consultations/{instance.consultation.public_id}/{uuid.uuid4().hex}.{ext}'


class SkinConsultation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('analyzing', 'Analyzing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    SKIN_TYPE_CHOICES = [
        ('', 'Not sure'),
        ('dry', 'Dry'),
        ('oily', 'Oily'),
        ('sensitive', 'Sensitive'),
        ('combination', 'Combination'),
        ('all', 'Normal / Balanced'),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='consultations',
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Questionnaire
    age_range = models.CharField(max_length=20, blank=True)
    declared_skin_type = models.CharField(
        max_length=20, choices=SKIN_TYPE_CHOICES, blank=True
    )
    primary_goals = models.TextField(
        blank=True, help_text='User-described goals / concerns'
    )
    sensitivity_level = models.PositiveSmallIntegerField(
        default=2, help_text='1=low … 5=high'
    )
    consent_analysis = models.BooleanField(default=False)
    consent_image_retention = models.BooleanField(
        default=False,
        help_text='If false, photos are deleted after analysis.',
    )

    # AI output
    detected_skin_type = models.CharField(max_length=20, blank=True)
    analysis_summary = models.TextField(blank=True)
    analysis_payload = models.JSONField(default=dict, blank=True)
    confidence_score = models.FloatField(default=0.0)
    analyzer_backend = models.CharField(max_length=40, blank=True)

    concerns = models.ManyToManyField(
        SkinConcern, related_name='consultations', blank=True
    )
    recommended_products = models.ManyToManyField(
        Product, related_name='consultation_recs', blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Consultation {self.public_id}'

    def get_absolute_url(self):
        return reverse('consultation:results', args=[self.public_id])

    def concern_codes(self):
        return list(self.concerns.values_list('code', flat=True))


class ConsultationPhoto(models.Model):
    ANGLE_CHOICES = [
        ('face', 'Full face'),
        ('cheek', 'Cheek'),
        ('forehead', 'Forehead'),
        ('other', 'Other'),
    ]

    consultation = models.ForeignKey(
        SkinConsultation, related_name='photos', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=consultation_upload_to)
    angle = models.CharField(max_length=20, choices=ANGLE_CHOICES, default='face')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'Photo {self.id} for {self.consultation.public_id}'
