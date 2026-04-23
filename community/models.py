from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Page(models.Model):
    slug = models.SlugField(unique=True, max_length=255)
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="HTML/Markdown content")
    meta_description = models.CharField(max_length=255, blank=True)
    featured_image = models.ImageField(upload_to='pages/', blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class News(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    excerpt = models.CharField(max_length=500)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='news/', blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    published = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']
        verbose_name_plural = 'News'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True, help_text='e.g. Student, Business owner')
    message = models.TextField()
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Announcement(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    active = models.BooleanField(default=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-starts_at']

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Discover Kenya page — dynamic content
# ---------------------------------------------------------------------------

class DiscoverAttraction(models.Model):
    """A top attraction shown as a card on /discover/."""
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    short_description = models.TextField(
        help_text='Shown on the card (keep under 250 chars).'
    )
    description = models.TextField(
        blank=True, help_text='Longer description (optional).'
    )
    image = models.ImageField(upload_to='discover/attractions/', blank=True, null=True,
        help_text='Ideal size: 800x600px')
    icon = models.CharField(
        max_length=50, blank=True, default='bi-geo-alt',
        help_text='Bootstrap Icon class (e.g. "bi-tree") or emoji'
    )
    sort_order = models.IntegerField(default=0)
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            i = 2
            while DiscoverAttraction.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class TravelEssential(models.Model):
    """Small info cards at the bottom of /discover/ (currency, language, etc.)."""
    title = models.CharField(max_length=100)
    value = models.CharField(max_length=255, help_text='e.g. "Kenyan Shilling (KES)"')
    icon = models.CharField(
        max_length=50, blank=True, default='bi-info-circle',
        help_text='Bootstrap Icon class (e.g. "bi-currency-exchange")'
    )
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return f'{self.title}: {self.value}'
