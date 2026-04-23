from django.contrib.auth.models import AbstractUser
from django.db import models


CITY_CHOICES = [
    ('seoul', 'Seoul'),
    ('busan', 'Busan'),
    ('incheon', 'Incheon'),
    ('daegu', 'Daegu'),
    ('daejeon', 'Daejeon'),
    ('gwangju', 'Gwangju'),
    ('other', 'Other'),
]

CATEGORY_CHOICES = [
    ('student', 'Student'),
    ('worker', 'Worker'),
    ('professional', 'Professional'),
    ('tourist', 'Tourist'),
    ('other', 'Other'),
]


class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)

    # Korea-specific fields
    korean_phone = models.CharField(max_length=20, blank=True)
    address_korea = models.TextField(blank=True)
    city = models.CharField(max_length=20, choices=CITY_CHOICES, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    arrival_date = models.DateField(blank=True, null=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def leader_role(self):
        """Returns the Leader object if this user is a leader, else None."""
        try:
            return self.leader_profile if self.leader_profile.is_active else None
        except Exception:
            return None

    @property
    def role_display(self):
        if self.is_superuser:
            return 'Super Admin'
        if self.is_admin:
            return 'Administrator'
        leader = self.leader_role
        if leader:
            return leader.get_role_display()
        if self.is_verified:
            return 'Verified Member'
        return 'Member'


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.email
