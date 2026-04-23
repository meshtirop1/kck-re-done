from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


def _gen_reference_code():
    year = timezone.now().year
    suffix = get_random_string(6, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
    return f'KCK-M-{year}-{suffix}'


class MembershipTier(models.Model):
    """Admin-editable membership tier. MVP assumes ONE active tier at a time."""
    name = models.CharField(max_length=100, default='KCK Individual Member')
    annual_amount = models.DecimalField(max_digits=10, decimal_places=0, default=50000,
        help_text='Annual fee in the currency below.')
    currency = models.CharField(max_length=10, default='KRW')
    description = models.TextField(blank=True,
        help_text='Short description shown on the membership page.')
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Membership Tier'

    def __str__(self):
        return f'{self.name} ({self.currency} {self.annual_amount:,.0f})'

    def formatted_amount(self):
        return f'{self.currency} {self.annual_amount:,.0f}'


class MembershipBenefit(models.Model):
    """An individual benefit of membership. Admin-editable list."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-check-circle-fill',
        help_text='Bootstrap Icon class, e.g. bi-shield-fill')
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Membership Benefit'

    def __str__(self):
        return self.title


class Membership(models.Model):
    STATUS_PENDING = 'pending_payment'
    STATUS_AWAITING = 'awaiting_verification'
    STATUS_ACTIVE = 'active'
    STATUS_REJECTED = 'rejected'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Payment'),
        (STATUS_AWAITING, 'Awaiting Verification'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    tier = models.ForeignKey(MembershipTier, on_delete=models.PROTECT, related_name='memberships')

    member_number = models.CharField(max_length=30, blank=True, null=True, unique=True,
        help_text='Assigned on first activation. Persistent across renewals.')
    reference_code = models.CharField(max_length=30, unique=True, default=_gen_reference_code,
        help_text='Unique code the member uses in their bank transfer description.')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    expected_amount = models.DecimalField(max_digits=10, decimal_places=0)
    currency = models.CharField(max_length=10, default='KRW')

    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    payment_declared_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='verified_memberships')
    verification_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    reminder_30_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_7_sent_at = models.DateTimeField(null=True, blank=True)
    expiry_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} · {self.reference_code} · {self.get_status_display()}'

    @property
    def is_active(self):
        if self.status != self.STATUS_ACTIVE:
            return False
        if self.period_end and self.period_end < timezone.now().date():
            return False
        return True

    @property
    def days_remaining(self):
        if not self.period_end:
            return None
        return max(0, (self.period_end - timezone.now().date()).days)

    @property
    def is_pending(self):
        return self.status in (self.STATUS_PENDING, self.STATUS_AWAITING)

    def formatted_amount(self):
        return f'{self.currency} {self.expected_amount:,.0f}'


class MembershipPayment(models.Model):
    """A declared payment against a membership. Multiple allowed if first is rejected."""
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='payments')
    claimed_amount = models.DecimalField(max_digits=10, decimal_places=0)
    claimed_date = models.DateField(help_text='Date the user says they sent the transfer.')
    proof_image = models.ImageField(upload_to='memberships/proof/', blank=True, null=True)
    notes = models.TextField(blank=True, help_text='Any note from the user about the transfer.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment {self.claimed_amount} on {self.claimed_date} for {self.membership.reference_code}'


class MembershipAuditLog(models.Model):
    """Immutable audit log for every membership-related action."""
    ACTION_CHOICES = [
        ('apply', 'Member applied'),
        ('declare_payment', 'Member declared payment'),
        ('verify', 'Treasurer verified payment'),
        ('reject', 'Treasurer rejected payment'),
        ('expire', 'Membership expired'),
        ('renew', 'Member renewed'),
        ('tier_edit', 'Tier edited'),
        ('bank_edit', 'Bank details edited'),
        ('benefit_edit', 'Benefits edited'),
        ('reminder_sent', 'Expiry reminder sent'),
        ('member_number_assigned', 'Member number assigned'),
    ]

    membership = models.ForeignKey(Membership, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='membership_audit_actions')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True,
        help_text='Free-form JSON for extra context (e.g. old/new values).')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Membership Audit Log'

    def __str__(self):
        ts = self.created_at.strftime('%Y-%m-%d %H:%M')
        actor = self.actor or 'system'
        return f'{ts} · {actor} · {self.get_action_display()}'
