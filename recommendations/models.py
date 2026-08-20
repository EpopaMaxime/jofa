from django.db import models
from django.utils.text import slugify
from products.models import Product


class SkinConcern(models.Model):
    """Catalog of skin concerns used by AI consultation and recommendations."""

    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    keywords = models.TextField(
        blank=True,
        help_text='Comma-separated keywords used by the heuristic analyzer.',
    )
    related_skin_types = models.CharField(
        max_length=120,
        blank=True,
        help_text='Comma-separated Product.skin_type values (dry,oily,...)',
    )
    severity_weight = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)[:64]
        super().save(*args, **kwargs)

    def keyword_list(self):
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]

    def skin_type_list(self):
        return [s.strip() for s in self.related_skin_types.split(',') if s.strip()]


class ConcernProductMap(models.Model):
    """Admin-managed mapping from a skin concern to catalog products."""

    concern = models.ForeignKey(
        SkinConcern, related_name='product_maps', on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, related_name='concern_maps', on_delete=models.CASCADE
    )
    priority = models.PositiveSmallIntegerField(
        default=10, help_text='Lower = higher priority'
    )
    role = models.CharField(
        max_length=40,
        blank=True,
        help_text='e.g. cleanser, serum, moisturizer, treatment, sunscreen',
    )
    notes = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['priority', 'id']
        unique_together = ('concern', 'product')

    def __str__(self):
        return f'{self.concern.code} → {self.product.name}'


class RoutineBundle(models.Model):
    """Suggested product routine / bundle for a skin profile."""

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True)
    skin_type = models.CharField(
        max_length=20,
        blank=True,
        help_text='Optional primary Product.skin_type target',
    )
    concerns = models.ManyToManyField(
        SkinConcern, related_name='routines', blank=True
    )
    products = models.ManyToManyField(
        Product, through='RoutineStep', related_name='routines', blank=True
    )
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:180]
        super().save(*args, **kwargs)


class RoutineStep(models.Model):
    STEP_CHOICES = [
        ('cleanser', 'Cleanser'),
        ('toner', 'Toner'),
        ('serum', 'Serum'),
        ('treatment', 'Treatment'),
        ('moisturizer', 'Moisturizer'),
        ('sunscreen', 'Sunscreen'),
        ('mask', 'Mask'),
        ('other', 'Other'),
    ]

    routine = models.ForeignKey(
        RoutineBundle, related_name='steps', on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    step_type = models.CharField(max_length=20, choices=STEP_CHOICES, default='other')
    order = models.PositiveSmallIntegerField(default=1)
    instructions = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ('routine', 'product')

    def __str__(self):
        return f'{self.routine.name} · step {self.order}: {self.product.name}'
