from django.conf import settings
from django.db import models
from django.utils import timezone


class IntegrationProvider(models.Model):
    CATEGORY_CHOICES = [
        ('payment', 'Payment gateway'),
        ('delivery', 'Delivery / logistics'),
        ('marketing', 'Marketing'),
        ('email', 'Communication / email'),
        ('other', 'Other'),
    ]

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    config = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} ({self.category})'

    def save(self, *args, **kwargs):
        if self.is_default:
            IntegrationProvider.objects.filter(
                category=self.category, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('requires_action', 'Requires action'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey(
        'orders.Order', related_name='payments', on_delete=models.CASCADE
    )
    provider = models.ForeignKey(
        IntegrationProvider,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='payments',
    )
    provider_slug = models.CharField(max_length=40, default='simulate')
    external_id = models.CharField(max_length=120, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='XAF')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment {self.id} · {self.status} · Order {self.order_id}'

    def mark_succeeded(self, external_id='', raw=None):
        self.status = 'succeeded'
        if external_id:
            self.external_id = external_id
        if raw is not None:
            self.raw_response = raw
        self.paid_at = timezone.now()
        self.save()
        order = self.order
        order.paid = True
        if order.status == 'pending':
            order.status = 'completed'
        order.save(update_fields=['paid', 'status', 'updated'])


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ready', 'Ready for pickup'),
        ('in_transit', 'In transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    order = models.ForeignKey(
        'orders.Order', related_name='shipments', on_delete=models.CASCADE
    )
    provider = models.ForeignKey(
        IntegrationProvider,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shipments',
    )
    provider_slug = models.CharField(max_length=40, default='manual')
    tracking_number = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    carrier_label = models.CharField(max_length=120, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Shipment {self.tracking_number or self.id} · Order {self.order_id}'
