"""Embassy Liaison Service — KCK facilitates member requests to the Kenyan Embassy.

IMPORTANT: KCK does NOT issue official government documents. This system is a
coordination/facilitation layer: members submit requests, KCK officials (leaders)
review them, guide members on requirements, and forward verified requests to the
Embassy of Kenya in Seoul for official processing.
"""
from django.db import models
from django.conf import settings


SERVICE_TYPE_CHOICES = [
    ('passport_new', 'New Passport Application'),
    ('passport_renewal', 'Passport Renewal'),
    ('passport_replacement', 'Passport Replacement (Lost/Damaged)'),
    ('emergency_travel', 'Emergency Travel Document (ETD)'),
    ('national_id', 'National ID Application/Renewal'),
    ('birth_certificate', 'Birth Certificate Application'),
    ('notarization', 'Document Notarization / Authentication'),
    ('citizen_registration', 'Citizen Registration (Diaspora)'),
    ('consular_letter', 'Consular Letter Request'),
    ('visa_kenya', 'Kenya Visa Information / Guidance'),
    ('appointment_booking', 'Embassy Appointment Booking Assistance'),
    ('other', 'Other Embassy Service'),
]


REQUEST_STATUS_CHOICES = [
    ('submitted', 'Submitted'),
    ('under_review', 'Under KCK Review'),
    ('additional_info', 'Additional Information Needed'),
    ('forwarded', 'Forwarded to Embassy'),
    ('embassy_processing', 'Being Processed by Embassy'),
    ('appointment_scheduled', 'Embassy Appointment Scheduled'),
    ('ready_for_pickup', 'Ready for Collection'),
    ('completed', 'Completed'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled by Member'),
]


PRIORITY_CHOICES = [
    ('normal', 'Normal'),
    ('urgent', 'Urgent'),
    ('emergency', 'Emergency'),
]


class EmbassyServiceRequest(models.Model):
    """A member's request for embassy service facilitation by KCK."""
    request_number = models.CharField(max_length=40, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='embassy_requests'
    )
    service_type = models.CharField(max_length=40, choices=SERVICE_TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=REQUEST_STATUS_CHOICES, default='submitted')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')

    full_name = models.CharField(max_length=255, help_text='As on Kenyan ID/Passport')
    kenyan_id_number = models.CharField(max_length=50, blank=True, help_text='National ID number')
    current_document_number = models.CharField(
        max_length=100, blank=True,
        help_text='Current passport/ID number if renewing or replacing'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    korean_phone = models.CharField(max_length=20, blank=True)
    address_in_korea = models.TextField()
    city = models.CharField(max_length=50, blank=True)

    purpose = models.TextField(help_text='Why you need this service')
    urgency_reason = models.TextField(blank=True, help_text='If urgent/emergency, explain why')
    preferred_appointment_date = models.DateField(null=True, blank=True)

    supporting_document_1 = models.FileField(upload_to='embassy_requests/', blank=True, null=True)
    supporting_document_2 = models.FileField(upload_to='embassy_requests/', blank=True, null=True)
    supporting_document_3 = models.FileField(upload_to='embassy_requests/', blank=True, null=True)

    consent_data_sharing = models.BooleanField(
        default=False,
        help_text='I consent to KCK forwarding my data to the Kenyan Embassy'
    )
    consent_privacy_policy = models.BooleanField(
        default=False,
        help_text='I have read and agree to the KCK privacy policy'
    )

    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='assigned_embassy_requests',
        help_text='KCK officer handling this request'
    )
    embassy_reference = models.CharField(
        max_length=100, blank=True,
        help_text='Embassy reference number once forwarded'
    )
    internal_notes = models.TextField(
        blank=True, help_text='Internal KCK notes (not visible to member)'
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    forwarded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def save(self, *args, **kwargs):
        if not self.request_number:
            from django.utils import timezone
            year = timezone.now().year
            last = EmbassyServiceRequest.objects.filter(
                request_number__startswith=f'KCK-ESR-{year}-'
            ).order_by('-request_number').first()
            if last:
                try:
                    n = int(last.request_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    n = 1
            else:
                n = 1
            self.request_number = f'KCK-ESR-{year}-{n:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.request_number} - {self.full_name} ({self.get_service_type_display()})'

    @property
    def status_badge_class(self):
        return {
            'submitted': 'secondary',
            'under_review': 'info',
            'additional_info': 'warning',
            'forwarded': 'primary',
            'embassy_processing': 'primary',
            'appointment_scheduled': 'success',
            'ready_for_pickup': 'success',
            'completed': 'success',
            'rejected': 'danger',
            'cancelled': 'dark',
        }.get(self.status, 'secondary')

    @property
    def is_editable_by_user(self):
        return self.status == 'submitted'

    # Template-friendly aliases
    @property
    def email(self):
        return self.user.email if self.user else ''

    @property
    def passport_number(self):
        return self.current_document_number

    @property
    def korean_address(self):
        return self.address_in_korea

    @property
    def description(self):
        return self.purpose

    @property
    def additional_details(self):
        return self.urgency_reason

    @property
    def created_at(self):
        return self.submitted_at

    @property
    def can_cancel(self):
        return self.status not in ('completed', 'rejected', 'cancelled')

    @property
    def documents(self):
        """Return a queryset-like list of document file fields that have a value."""
        class _Docs:
            def __init__(self, files):
                self._files = files
            def all(self):
                return self._files
            def __bool__(self):
                return bool(self._files)
        docs = []
        for i, f in enumerate([self.supporting_document_1, self.supporting_document_2, self.supporting_document_3], start=1):
            if f:
                class _Doc:
                    def __init__(self, file_field, idx):
                        self.file = file_field
                        self.url = file_field.url
                        self.name = file_field.name.split('/')[-1]
                        self.idx = idx
                docs.append(_Doc(f, i))
        return _Docs(docs)

    @property
    def status_order(self):
        """Numeric progression for timeline display."""
        order = {
            'submitted': 1, 'under_review': 2, 'additional_info': 2,
            'forwarded': 3, 'embassy_processing': 3, 'appointment_scheduled': 3,
            'ready_for_pickup': 4, 'completed': 5, 'rejected': 5, 'cancelled': 0,
        }
        return order.get(self.status, 0)

    @property
    def priority_badge_class(self):
        return {'normal': 'secondary', 'urgent': 'warning', 'emergency': 'danger'}.get(self.priority, 'secondary')


class RequestNote(models.Model):
    """A note/update/message on a service request, for communication log."""
    NOTE_TYPE_CHOICES = [
        ('member_message', 'Message from Member'),
        ('officer_reply', 'Reply from KCK Officer'),
        ('status_change', 'Status Change'),
        ('system', 'System Update'),
    ]

    request = models.ForeignKey(EmbassyServiceRequest, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='member_message')
    message = models.TextField()
    attachment = models.FileField(upload_to='embassy_requests/notes/', blank=True, null=True)
    is_internal = models.BooleanField(
        default=False, help_text='If true, only visible to KCK officers (not the member)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Note on {self.request.request_number}'


class ServiceGuide(models.Model):
    """Informational guide for each service type — requirements, fees, timelines."""
    service_type = models.CharField(max_length=40, choices=SERVICE_TYPE_CHOICES, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.JSONField(
        default=list,
        help_text='List of required documents/information'
    )
    typical_timeline = models.CharField(max_length=100, blank=True, help_text='e.g. "2-4 weeks"')
    embassy_fee = models.CharField(max_length=100, blank=True, help_text='Fees charged by Embassy')
    kck_facilitation_fee = models.CharField(max_length=100, default='Free', help_text='Fees charged by KCK (if any)')
    icon = models.CharField(max_length=10, blank=True, default='📋')
    additional_info = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title
