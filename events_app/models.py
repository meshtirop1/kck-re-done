from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Event(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    registration_deadline = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_past(self):
        from django.utils import timezone
        return self.date < timezone.now()

    @property
    def registration_count(self):
        return self.registrations.count()

    @property
    def spots_available(self):
        if not self.capacity:
            return None
        return self.capacity - self.registration_count


REG_STATUS_CHOICES = [
    ('registered', 'Registered'),
    ('cancelled', 'Cancelled'),
    ('attended', 'Attended'),
]


class EventRegistration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=20, choices=REG_STATUS_CHOICES, default='registered')
    notes = models.TextField(blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'event']]
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


class EventGalleryImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Image for {self.event.title}"
