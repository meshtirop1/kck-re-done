"""Permission audit log — separate file so existing leaders/models.py stays clean."""
from django.conf import settings
from django.db import models


class PermissionAuditLog(models.Model):
    leader = models.ForeignKey('leaders.Leader', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='permission_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='permission_audit_actions')
    flag = models.CharField(max_length=60, blank=True,
        help_text='The permission flag that was changed; blank if "all" / role default reset.')
    old_value = models.BooleanField(null=True, blank=True)
    new_value = models.BooleanField(null=True, blank=True)
    summary = models.CharField(max_length=255, blank=True,
        help_text='Human description e.g. "Reset to role defaults" or "Granted can_view_audit_log".')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Permission Audit Log'

    def __str__(self):
        ts = self.created_at.strftime('%Y-%m-%d %H:%M')
        actor = self.actor or 'system'
        target = self.leader.user if self.leader else '(deleted)'
        return f'{ts} · {actor} → {target}: {self.summary or self.flag}'
