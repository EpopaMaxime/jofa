from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Vendor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending review'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor',
    )
    store_name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='vendors/logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='vendors/banners/', blank=True, null=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='Cameroon')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text='Platform commission % on sales',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['store_name']

    def __str__(self):
        return self.store_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.store_name)[:160] or 'vendor'
            slug = base
            i = 2
            while Vendor.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        if not self.email and self.user_id:
            self.email = self.user.email
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('vendors:storefront', args=[self.slug])

    @property
    def is_selling(self):
        return self.is_active and self.status == 'approved'

    def product_count(self):
        return self.products.filter(available=True).count()
