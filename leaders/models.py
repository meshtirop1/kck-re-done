from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


LEADER_ROLE_CHOICES = [
    ('president', 'President'),
    ('vice_president', 'Vice President'),
    ('secretary', 'Secretary General'),
    ('treasurer', 'Treasurer'),
    ('welfare', 'Welfare Officer'),
    ('committee', 'Committee Member'),
]


class Leader(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leader_profile')
    role = models.CharField(max_length=30, choices=LEADER_ROLE_CHOICES)
    title = models.CharField(max_length=255, blank=True, help_text='Display title, e.g. "President of KCK"')
    bio = models.TextField(blank=True)
    message = models.TextField(blank=True,
        help_text='Official public message / statement from this leader (e.g. the President\'s Message shown on the homepage).')
    message_title = models.CharField(max_length=200, blank=True,
        help_text='Heading for the message, e.g. "A Message from Our President".')
    show_message_on_home = models.BooleanField(default=False,
        help_text='Feature this leader\'s message on the homepage.')
    photo = models.ImageField(upload_to='leaders/', blank=True, null=True)
    signature = models.ImageField(upload_to='leaders/signatures/', blank=True, null=True, help_text='Signature image for documents')
    stamp = models.ImageField(upload_to='leaders/stamps/', blank=True, null=True)
    email_official = models.EmailField(blank=True)
    phone_official = models.CharField(max_length=20, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    appointed_at = models.DateField(null=True, blank=True)
    term_ends = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'role']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} \u2014 {self.get_role_display()}"


# --- Permission catalog ----------------------------------------------------
# Every permission flag below maps to one tangible action a leader can perform
# on the platform. The president (or a superuser) toggles these per leader at
# /portal/roles/. Defaults below seed sensible starting permissions per role.

PERMISSION_CATALOG = [
    # (flag_name, label, description, group)
    ('can_manage_leaders',         'Manage leaders & assign roles',
        'Add, remove and edit other leaders. Change who can do what (this page itself).',
        'Governance'),
    ('can_manage_users',           'Manage member accounts',
        'View, edit and deactivate user accounts.',
        'Members'),
    ('can_verify_users',           'Verify member identity',
        'Mark members as identity-verified after document checks.',
        'Members'),
    ('can_export_users',           'Export member lists',
        'Download member registries as CSV.',
        'Members'),
    ('can_manage_memberships',     'Manage paid memberships (treasurer)',
        'Verify payments, edit fees, manage benefits, run CSV bank import.',
        'Membership'),
    ('can_view_financials',        'View financial reports',
        'See collected amounts, payment audit log, treasurer reports.',
        'Membership'),
    ('can_review_embassy_requests','Review embassy liaison requests',
        'Process embassy-service requests from members.',
        'Workflows'),
    ('can_review_endorsements',    'Issue & sign endorsements',
        'Approve and sign cover-letter / endorsement requests.',
        'Workflows'),
    ('can_issue_certificates',     'Issue certificates',
        'Create and sign membership / community certificates.',
        'Workflows'),
    ('can_review_market_sellers',  'Review Kenyan Market sellers',
        'Approve, reject or suspend seller applications.',
        'Workflows'),
    ('can_send_communications',    'Send official communications',
        'Publish letters, announcements and emails to members.',
        'Communications'),
    ('can_manage_events',          'Manage events',
        'Create, edit and delete community events.',
        'Content'),
    ('can_manage_content',         'Manage site content',
        'Edit visa info, FAQs, news, attractions, testimonials, banners, content pages.',
        'Content'),
    ('can_manage_settings',        'Manage site settings',
        'Edit global site settings (branding, bank, contact, etc.).',
        'Governance'),
    ('can_view_analytics',         'View analytics',
        'View site usage, membership and engagement analytics.',
        'Analytics'),
    ('can_view_audit_log',         'View audit log',
        'Read the immutable record of every membership / permission action.',
        'Governance'),
]

PERMISSION_FLAGS = [p[0] for p in PERMISSION_CATALOG]


ROLE_DEFAULT_PERMISSIONS = {
    'president': {p: True for p in PERMISSION_FLAGS},  # everything
    'vice_president': {
        'can_manage_users': True, 'can_verify_users': True,
        'can_send_communications': True, 'can_manage_events': True,
        'can_review_endorsements': True, 'can_review_embassy_requests': True,
        'can_view_analytics': True, 'can_view_audit_log': True,
    },
    'secretary': {
        'can_manage_users': True, 'can_verify_users': True, 'can_export_users': True,
        'can_send_communications': True, 'can_manage_events': True,
        'can_manage_content': True, 'can_review_endorsements': True,
        'can_review_embassy_requests': True, 'can_view_audit_log': True,
    },
    'treasurer': {
        'can_manage_memberships': True, 'can_view_financials': True,
        'can_view_analytics': True, 'can_view_audit_log': True,
    },
    'welfare': {
        'can_issue_certificates': True, 'can_send_communications': True,
        'can_review_embassy_requests': True,
    },
    'committee': {
        'can_manage_events': True, 'can_review_market_sellers': True,
    },
}


class LeaderPermission(models.Model):
    leader = models.OneToOneField(Leader, on_delete=models.CASCADE, related_name='permissions')

    # Governance
    can_manage_leaders = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    can_view_audit_log = models.BooleanField(default=False)

    # Members
    can_manage_users = models.BooleanField(default=False)
    can_verify_users = models.BooleanField(default=False)
    can_export_users = models.BooleanField(default=False)

    # Membership / finances
    can_manage_memberships = models.BooleanField(default=False)
    can_view_financials = models.BooleanField(default=False)

    # Workflows
    can_review_embassy_requests = models.BooleanField(default=False)
    can_review_endorsements = models.BooleanField(default=False)
    can_issue_certificates = models.BooleanField(default=False)
    can_review_market_sellers = models.BooleanField(default=False)

    # Communications & content
    can_send_communications = models.BooleanField(default=False)
    can_manage_events = models.BooleanField(default=False)
    can_manage_content = models.BooleanField(default=False)

    # Insights
    can_view_analytics = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Permissions for {self.leader}"

    def as_dict(self):
        return {p: getattr(self, p) for p in PERMISSION_FLAGS}


@receiver(post_save, sender=Leader)
def create_leader_permissions(sender, instance, created, **kwargs):
    perms, _ = LeaderPermission.objects.get_or_create(leader=instance)
    if created:
        defaults = ROLE_DEFAULT_PERMISSIONS.get(instance.role, {})
        for attr, value in defaults.items():
            setattr(perms, attr, value)
        perms.save()


# Re-export the audit model so it's collected by makemigrations
from .audit_models import PermissionAuditLog  # noqa: E402, F401
