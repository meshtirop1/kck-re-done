"""KCK Endorsement / Cover Note system.

Formal letters from KCK leadership endorsing, introducing, or verifying a
community member. Common uses:
  - Cover note accompanying an embassy service request (passport, visa, etc.)
  - Letter of introduction for banks, schools, employers
  - Verification of KCK membership
  - Recommendation letter

Every endorsement has a unique reference number and a verification UUID so that
recipients (e.g. the embassy, a bank) can verify authenticity on the KCK site.
"""
import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse


ENDORSEMENT_TYPE_CHOICES = [
    ('cover_note', 'Cover Note'),
    ('endorsement', 'Letter of Endorsement'),
    ('introduction', 'Letter of Introduction'),
    ('recommendation', 'Letter of Recommendation'),
    ('verification', 'Membership Verification Letter'),
    ('to_whom', 'To Whom It May Concern'),
]

ENDORSEMENT_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('generating', 'Generating PDF'),
    ('issued', 'Issued'),
    ('revoked', 'Revoked'),
    ('expired', 'Expired'),
]


class Endorsement(models.Model):
    reference_number = models.CharField(max_length=40, unique=True, editable=False)
    verification_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='endorsements_received',
        help_text='The KCK member being endorsed (leave blank if non-member)'
    )
    member_full_name = models.CharField(
        max_length=255, help_text='Full name as it should appear on the letter'
    )
    member_id_number = models.CharField(
        max_length=100, blank=True, help_text='Kenyan National ID / Passport number'
    )

    endorsement_type = models.CharField(
        max_length=30, choices=ENDORSEMENT_TYPE_CHOICES, default='cover_note'
    )
    subject = models.CharField(
        max_length=255, help_text='e.g. "Cover Note for Passport Renewal Application"'
    )
    addressed_to = models.CharField(
        max_length=255, blank=True,
        help_text='e.g. "The Ambassador, Kenyan Embassy in Seoul" — leave blank for "To Whom It May Concern"'
    )
    addressed_to_address = models.TextField(
        blank=True, help_text='Recipient address (optional)'
    )
    purpose = models.CharField(
        max_length=500, help_text='Brief statement of purpose'
    )
    body = models.TextField(
        help_text='Main body of the endorsement letter'
    )
    member_standing = models.TextField(
        blank=True,
        help_text='Description of member standing (e.g. "A registered active member since 2023")'
    )

    related_service_request = models.ForeignKey(
        'embassy_liaison.EmbassyServiceRequest', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='endorsements',
        help_text='Link to an existing embassy service request (optional)'
    )

    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(
        null=True, blank=True, help_text='Leave blank if endorsement does not expire'
    )

    issued_by = models.ForeignKey(
        'leaders.Leader', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='endorsements_issued'
    )
    issued_by_name = models.CharField(max_length=255, blank=True)
    issued_by_role = models.CharField(max_length=255, blank=True)

    pdf_file = models.FileField(upload_to='endorsements/pdf/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=ENDORSEMENT_STATUS_CHOICES, default='draft')
    revoke_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='endorsements_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    issued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference_number:
            from django.utils import timezone
            year = timezone.now().year
            last = Endorsement.objects.filter(
                reference_number__startswith=f'KCK-END-{year}-'
            ).order_by('-reference_number').first()
            if last:
                try:
                    n = int(last.reference_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    n = 1
            else:
                n = 1
            self.reference_number = f'KCK-END-{year}-{n:04d}'
        if not self.valid_from:
            from django.utils import timezone
            self.valid_from = timezone.now().date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.reference_number} - {self.member_full_name}'

    def get_verification_url(self, request=None):
        path = reverse('endorsements:verify', args=[str(self.verification_code)])
        if request:
            return request.build_absolute_uri(path)
        return path

    @property
    def status_badge_class(self):
        return {
            'draft': 'secondary', 'generating': 'info', 'issued': 'success',
            'revoked': 'danger', 'expired': 'dark',
        }.get(self.status, 'secondary')

    @property
    def is_valid(self):
        from django.utils import timezone
        if self.status != 'issued':
            return False
        today = timezone.now().date()
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_until and today > self.valid_until:
            return False
        return True
