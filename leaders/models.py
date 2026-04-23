from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


LEADER_ROLE_CHOICES = [
    ('president', 'President'),
    ('vice_president', 'Vice President'),
    ('secretary', 'Secretary'),
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


ROLE_DEFAULT_PERMISSIONS = {
    'president': {
        'can_manage_users': True, 'can_verify_users': True, 'can_export_users': True,
        'can_manage_memberships': True, 'can_view_financials': True, 'can_send_communications': True,
        'can_issue_certificates': True, 'can_manage_events': True, 'can_manage_leaders': True,
        'can_view_analytics': True,
    },
    'vice_president': {
        'can_manage_users': True, 'can_verify_users': True, 'can_send_communications': True,
        'can_manage_events': True, 'can_view_analytics': True,
    },
    'secretary': {
        'can_manage_users': True, 'can_verify_users': True, 'can_export_users': True,
        'can_send_communications': True, 'can_manage_events': True,
    },
    'treasurer': {
        'can_manage_memberships': True, 'can_view_financials': True, 'can_view_analytics': True,
    },
    'welfare': {
        'can_issue_certificates': True, 'can_send_communications': True,
    },
    'committee': {
        'can_manage_events': True,
    },
}


class LeaderPermission(models.Model):
    leader = models.OneToOneField(Leader, on_delete=models.CASCADE, related_name='permissions')
    can_manage_users = models.BooleanField(default=False)
    can_verify_users = models.BooleanField(default=False)
    can_export_users = models.BooleanField(default=False)
    can_manage_memberships = models.BooleanField(default=False)
    can_view_financials = models.BooleanField(default=False)
    can_send_communications = models.BooleanField(default=False)
    can_issue_certificates = models.BooleanField(default=False)
    can_manage_events = models.BooleanField(default=False)
    can_manage_leaders = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)

    def __str__(self):
        return f"Permissions for {self.leader}"


@receiver(post_save, sender=Leader)
def create_leader_permissions(sender, instance, created, **kwargs):
    perms, _ = LeaderPermission.objects.get_or_create(leader=instance)
    if created:
        defaults = ROLE_DEFAULT_PERMISSIONS.get(instance.role, {})
        for attr, value in defaults.items():
            setattr(perms, attr, value)
        perms.save()
