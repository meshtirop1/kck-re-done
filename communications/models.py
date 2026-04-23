from django.db import models
from django.conf import settings


COMM_CATEGORY_CHOICES = [
    ('general', 'General Notice'),
    ('urgent', 'Urgent'),
    ('welfare', 'Welfare'),
    ('event', 'Event Communication'),
    ('emergency', 'Emergency'),
    ('condolence', 'Condolence'),
    ('celebration', 'Celebration'),
]

COMM_AUDIENCE_CHOICES = [
    ('all', 'Everyone (Public)'),
    ('members', 'Registered Members Only'),
    ('city', 'Specific City'),
    ('category', 'Specific User Category'),
]

COMM_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('processing', 'Processing'),
    ('published', 'Published'),
    ('archived', 'Archived'),
]


class Communication(models.Model):
    """Official letters/communications issued by KCK leadership."""
    reference_number = models.CharField(max_length=40, unique=True, editable=False)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    category = models.CharField(max_length=20, choices=COMM_CATEGORY_CHOICES, default='general')
    audience = models.CharField(max_length=20, choices=COMM_AUDIENCE_CHOICES, default='all')
    audience_filter = models.CharField(max_length=100, blank=True, help_text='City slug or category slug for filtered audience')
    sender = models.ForeignKey('leaders.Leader', on_delete=models.SET_NULL, null=True, blank=True, related_name='communications_sent')
    sender_name_override = models.CharField(max_length=255, blank=True)
    sender_role_override = models.CharField(max_length=255, blank=True)
    cover_image = models.ImageField(upload_to='communications/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='communications/pdf/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=COMM_STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.reference_number:
            from django.utils import timezone
            year = timezone.now().year
            last = Communication.objects.filter(reference_number__startswith=f'KCK/{year}/').order_by('-reference_number').first()
            if last:
                try:
                    n = int(last.reference_number.split('/')[-1]) + 1
                except (ValueError, IndexError):
                    n = 1
            else:
                n = 1
            self.reference_number = f'KCK/{year}/{n:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.reference_number} - {self.subject}'


class Announcement(models.Model):
    """Public community announcements (news/updates)."""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('welfare', 'Welfare'),
        ('event', 'Event'),
        ('notice', 'Official Notice'),
        ('condolence', 'Condolence'),
        ('celebration', 'Celebration'),
        ('urgent', 'Urgent'),
    ]
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    cover_image = models.ImageField(upload_to='announcements/', blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_published = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.title)
            slug = base
            i = 2
            while Announcement.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        if self.is_published and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CommunicationDelivery(models.Model):
    """Tracks delivery of a communication to a recipient."""
    communication = models.ForeignKey(Communication, on_delete=models.CASCADE, related_name='deliveries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('communication', 'user')]
