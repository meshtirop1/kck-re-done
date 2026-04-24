from django.contrib import admin
from .models import Leader, LeaderPermission
from .audit_models import PermissionAuditLog


@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'leader', 'flag', 'old_value', 'new_value', 'summary')
    list_filter = ('flag', 'new_value')
    search_fields = ('actor__username', 'leader__user__username', 'summary')
    readonly_fields = [f.name for f in PermissionAuditLog._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class LeaderPermissionInline(admin.StackedInline):
    model = LeaderPermission
    can_delete = False
    extra = 0


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'title', 'is_active', 'sort_order')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'user__email', 'title')
    list_editable = ('sort_order', 'is_active')
    inlines = [LeaderPermissionInline]


@admin.register(LeaderPermission)
class LeaderPermissionAdmin(admin.ModelAdmin):
    list_display = (
        'leader',
        'can_manage_users',
        'can_verify_users',
        'can_manage_memberships',
        'can_view_financials',
        'can_manage_events',
    )
    search_fields = ('leader__user__username', 'leader__user__email')
