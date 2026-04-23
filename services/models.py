from django.db import models
from django.conf import settings
from django.utils.text import slugify


class VisaType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField()
    requirements = models.JSONField(default=list, help_text="List of requirements")
    processing_time = models.CharField(max_length=100)
    fee = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, blank=True, default='📋')
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('under_review', 'Under Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('additional_info_needed', 'Additional Info Needed'),
]


class VisaApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visa_applications')
    visa_type = models.ForeignKey(VisaType, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=100)
    passport_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    purpose_of_visit = models.TextField()
    intended_arrival = models.DateField()
    intended_departure = models.DateField()
    supporting_document = models.FileField(upload_to='visa_documents/', blank=True, null=True)
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reviewed_visa_applications',
    )

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.visa_type.name} ({self.status})"

    @property
    def status_badge_class(self):
        return {
            'pending': 'warning',
            'under_review': 'info',
            'approved': 'success',
            'rejected': 'danger',
            'additional_info_needed': 'secondary',
        }.get(self.status, 'secondary')


PASSPORT_TYPE_CHOICES = [
    ('new', 'New Passport'),
    ('renewal', 'Renewal'),
    ('replacement', 'Replacement'),
]

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
]


class PassportApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='passport_applications')
    type = models.CharField(max_length=20, choices=PASSPORT_TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    national_id = models.CharField(max_length=50)
    current_passport_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address_in_korea = models.TextField()
    address_in_kenya = models.TextField()
    supporting_document = models.FileField(upload_to='passport_documents/', blank=True, null=True)
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reviewed_passport_applications',
    )

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.full_name} - {self.get_type_display()}"

    @property
    def status_badge_class(self):
        return VisaApplication.status_badge_class.fget(self)


CATEGORY_CHOICES = [
    ('general', 'General'),
    ('visa', 'Visa'),
    ('passport', 'Passport'),
    ('consular', 'Consular'),
]


class Faq(models.Model):
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'sort_order']

    def __str__(self):
        return self.question
