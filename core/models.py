from django.db import models
from django.utils.text import slugify

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "FAQs"
        ordering = ['order']

    def __str__(self):
        return self.question

class Partner(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='partners/', blank=True, null=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    role = models.CharField(max_length=100)
    bio = models.TextField(help_text="Short introductory bio.")
    full_bio = models.TextField(blank=True, null=True, help_text="Detailed biography for the dedicated member page.")
    education = models.CharField(max_length=255, blank=True, null=True)
    expertise = models.CharField(max_length=255, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='team/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.role}"

class NewsEvent(models.Model):
    TYPE_CHOICES = [
        ('news', 'News'),
        ('event', 'Event'),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='news')
    content = models.TextField()
    excerpt = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='news_events/', blank=True, null=True)
    date = models.DateField(blank=True, null=True, help_text="For events, this is the event date.")
    location = models.CharField(max_length=200, blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "News & Event"
        verbose_name_plural = "News & Events"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"
