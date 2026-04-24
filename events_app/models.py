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
    members_only = models.BooleanField(default=False,
        help_text='If on, only paid-up KCK members can register for this event.')
    waitlist_enabled = models.BooleanField(default=True,
        help_text='If on, users who register after capacity is reached are added to a waitlist and promoted automatically when seats open up.')
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
        """Count of CONFIRMED registrations only (excludes waitlist + cancelled)."""
        return self.registrations.filter(status='registered').count()

    @property
    def waitlist_count(self):
        return self.registrations.filter(status='waitlisted').count()

    @property
    def spots_available(self):
        if not self.capacity:
            return None
        return max(0, self.capacity - self.registration_count)

    @property
    def is_full(self):
        return bool(self.capacity) and self.registration_count >= self.capacity

    @property
    def deadline_passed(self):
        """True if a registration deadline is set and we're past it."""
        if not self.registration_deadline:
            return False
        from django.utils import timezone
        return timezone.now() > self.registration_deadline

    @property
    def registration_open(self):
        """One-stop check: can a NEW user still register/waitlist for this event?"""
        if not self.active or self.is_past or self.deadline_passed:
            return False
        return True

    @property
    def spots_low(self):
        """True when ≤5 spots remain and event is not yet full — for warning UI."""
        if not self.capacity:
            return False
        remaining = self.spots_available
        return 0 < remaining <= 5


REG_STATUS_CHOICES = [
    ('registered', 'Registered'),
    ('waitlisted', 'On Waitlist'),
    ('cancelled', 'Cancelled'),
    ('attended', 'Attended'),
]


class EventRegistration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=20, choices=REG_STATUS_CHOICES, default='registered')
    waitlist_position = models.PositiveIntegerField(blank=True, null=True,
        help_text='Position in the waitlist queue (1 = next in line). Null when registered.')
    is_member = models.BooleanField(default=False,
        help_text='Snapshot of membership status at registration time (used for waitlist priority).')
    notes = models.TextField(blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    promoted_at = models.DateTimeField(blank=True, null=True,
        help_text='When (if) this registration was promoted from waitlist to confirmed.')
    cancelled_at = models.DateTimeField(blank=True, null=True)
    promotion_email_sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = [['user', 'event']]
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.get_status_display()})"


class EventGalleryImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Image for {self.event.title}"
