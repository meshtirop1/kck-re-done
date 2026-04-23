import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse

CERT_TYPE_CHOICES = [
    ('appreciation', 'Certificate of Appreciation'),
    ('participation', 'Certificate of Participation'),
    ('leadership', 'Leadership Certificate'),
    ('welfare', 'Welfare Certificate'),
    ('membership', 'Membership Certificate'),
    ('recognition', 'Certificate of Recognition'),
    ('custom', 'Custom Certificate'),
]

CERT_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('generating', 'Generating'),
    ('published', 'Published'),
    ('revoked', 'Revoked'),
    ('failed', 'Failed'),
]


class Certificate(models.Model):
    cert_number = models.CharField(max_length=40, unique=True, editable=False)
    verification_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='certificates_received',
        help_text='Leave blank if recipient is not a registered user'
    )
    recipient_name = models.CharField(max_length=255, help_text='Full name as it should appear on certificate')
    cert_type = models.CharField(max_length=30, choices=CERT_TYPE_CHOICES, default='appreciation')
    title = models.CharField(max_length=255, blank=True, help_text='Custom title (for custom type)')
    body = models.TextField(help_text='Body text shown on certificate')
    event_title = models.CharField(max_length=255, blank=True, help_text='Related event/occasion (optional)')
    issued_date = models.DateField(auto_now_add=False, null=True, blank=True)
    issued_by = models.ForeignKey('leaders.Leader', on_delete=models.SET_NULL, null=True, blank=True, related_name='certificates_issued')
    issued_by_name = models.CharField(max_length=255, blank=True, help_text='Name override if no leader selected')
    issued_by_role = models.CharField(max_length=255, blank=True, help_text='Role override if no leader selected')
    pdf_file = models.FileField(upload_to='certificates/pdf/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=CERT_STATUS_CHOICES, default='draft')
    revoke_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificates_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.cert_number:
            from django.utils import timezone
            year = timezone.now().year
            last = Certificate.objects.filter(cert_number__startswith=f'KCK-CERT-{year}-').order_by('-cert_number').first()
            if last:
                try:
                    n = int(last.cert_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    n = 1
            else:
                n = 1
            self.cert_number = f'KCK-CERT-{year}-{n:04d}'
        if not self.issued_date:
            from django.utils import timezone
            self.issued_date = timezone.now().date()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('certificates:detail', args=[self.pk])

    def get_verification_url(self, request=None):
        path = reverse('certificates:verify', args=[str(self.verification_code)])
        if request:
            return request.build_absolute_uri(path)
        return path

    def __str__(self):
        return f"{self.cert_number} \u2014 {self.recipient_name}"
