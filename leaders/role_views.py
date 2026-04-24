"""Role & permission management — only the President or a superuser can use these."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from functools import wraps

from .audit_models import PermissionAuditLog
from .models import (Leader, LeaderPermission, ROLE_DEFAULT_PERMISSIONS,
                     PERMISSION_CATALOG, PERMISSION_FLAGS)
from .permissions import can_manage_roles


def _client_ip(request):
    xf = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return xf.split(',')[0].strip() if xf else request.META.get('REMOTE_ADDR')


def role_admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not can_manage_roles(request.user):
            raise PermissionDenied(
                'Only the President or a website Administrator may manage role permissions.'
            )
        return view(request, *args, **kwargs)
    return wrapped


def _grouped_catalog(perms=None, defaults=None):
    """Group PERMISSION_CATALOG by their group label, preserving order.

    If `perms` (a LeaderPermission instance) is provided, each item gains an
    `is_on` boolean reflecting whether that flag is currently set on the leader.
    If `defaults` (dict) is provided, each item also gains a `default_on` flag.
    """
    groups = {}
    for flag, label, desc, group in PERMISSION_CATALOG:
        groups.setdefault(group, []).append({
            'flag': flag, 'label': label, 'desc': desc,
            'is_on': bool(getattr(perms, flag, False)) if perms else False,
            'default_on': bool(defaults.get(flag, False)) if defaults else False,
        })
    return groups


@role_admin_required
def roles_overview(request):
    """Matrix view: rows = leaders, columns = permissions."""
    leaders = (Leader.objects.filter(is_active=True)
               .select_related('user', 'permissions')
               .order_by('sort_order', 'role'))
    rows = []
    for l in leaders:
        perms = getattr(l, 'permissions', None)
        rows.append({
            'leader': l,
            'count_on': sum(1 for f in PERMISSION_FLAGS if perms and getattr(perms, f)),
            'flags': {f: bool(perms and getattr(perms, f)) for f in PERMISSION_FLAGS},
        })
    return render(request, 'leaders/roles_overview.html', {
        'rows': rows,
        'catalog_groups': _grouped_catalog(),
        'total_perms': len(PERMISSION_FLAGS),
        'role_defaults': ROLE_DEFAULT_PERMISSIONS,
    })


@role_admin_required
def role_edit(request, pk):
    leader = get_object_or_404(Leader.objects.select_related('user', 'permissions'), pk=pk)
    perms, _ = LeaderPermission.objects.get_or_create(leader=leader)

    if request.method == 'POST':
        changed = []
        for flag in PERMISSION_FLAGS:
            old = bool(getattr(perms, flag))
            new = request.POST.get(flag) == 'on'
            if old != new:
                setattr(perms, flag, new)
                changed.append((flag, old, new))
        if changed:
            perms.save()
            for flag, old, new in changed:
                PermissionAuditLog.objects.create(
                    leader=leader, actor=request.user, flag=flag,
                    old_value=old, new_value=new,
                    summary=f'{"Granted" if new else "Revoked"} "{flag}" for {leader.user.username}',
                    ip_address=_client_ip(request),
                )
            messages.success(request, f'Updated {len(changed)} permission(s) for {leader.user.get_full_name() or leader.user.username}.')
        else:
            messages.info(request, 'No changes.')
        return redirect('leaders:role_edit', pk=leader.pk)

    role_defaults = ROLE_DEFAULT_PERMISSIONS.get(leader.role, {})
    return render(request, 'leaders/role_edit.html', {
        'leader': leader,
        'perms': perms,
        'catalog_groups': _grouped_catalog(perms=perms, defaults=role_defaults),
        'role_defaults': role_defaults,
    })


@role_admin_required
def role_reset_defaults(request, pk):
    leader = get_object_or_404(Leader, pk=pk)
    perms, _ = LeaderPermission.objects.get_or_create(leader=leader)
    if request.method == 'POST':
        defaults = ROLE_DEFAULT_PERMISSIONS.get(leader.role, {})
        for flag in PERMISSION_FLAGS:
            setattr(perms, flag, defaults.get(flag, False))
        perms.save()
        PermissionAuditLog.objects.create(
            leader=leader, actor=request.user,
            summary=f'Reset all permissions to defaults for role "{leader.get_role_display()}"',
            ip_address=_client_ip(request),
        )
        messages.success(request, f'Permissions for {leader.user.get_full_name() or leader.user.username} reset to defaults for {leader.get_role_display()}.')
    return redirect('leaders:role_edit', pk=leader.pk)


@role_admin_required
def role_audit_log(request):
    qs = PermissionAuditLog.objects.select_related('actor', 'leader__user').order_by('-created_at')
    page_obj = Paginator(qs, 50).get_page(request.GET.get('page'))
    return render(request, 'leaders/role_audit.html', {'page_obj': page_obj})
