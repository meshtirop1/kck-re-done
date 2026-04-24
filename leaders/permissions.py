"""Centralised permission helpers — use these everywhere instead of hardcoding role checks.

Examples:
    from leaders.permissions import user_has_perm, permission_required

    if user_has_perm(request.user, 'can_manage_memberships'):
        ...

    @permission_required('can_review_market_sellers')
    def review_seller(request, pk):
        ...
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import PERMISSION_FLAGS


def user_has_perm(user, flag):
    """Return True if `user` may perform action `flag`.

    Rules:
    - Anonymous users: never.
    - Superusers: always.
    - Users marked is_admin (custom flag): always.
    - Active leaders: True if their LeaderPermission has the flag set.
    - Inactive leaders: never.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if getattr(user, 'is_admin', False):
        return True
    if flag not in PERMISSION_FLAGS:
        return False
    leader = getattr(user, 'leader_role', None)
    if not leader:
        return False
    perms = getattr(leader, 'permissions', None)
    if not perms:
        return False
    return bool(getattr(perms, flag, False))


def user_perm_set(user):
    """Return the set of permission flags the user holds (empty if none)."""
    return {flag for flag in PERMISSION_FLAGS if user_has_perm(user, flag)}


def permission_required(flag):
    """Decorator: raises PermissionDenied (403) if user lacks the permission.

    Anonymous users are bounced to the login page first.
    Authenticated users without the permission see the branded 403.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if not user_has_perm(request.user, flag):
                raise PermissionDenied(
                    f'This action requires the "{flag}" permission. '
                    f'Contact the President or an Administrator if you believe you should have access.'
                )
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def any_permission_required(*flags):
    """Decorator: user must hold at least ONE of the listed permissions."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if not any(user_has_perm(request.user, f) for f in flags):
                raise PermissionDenied(
                    f'This action requires one of: {", ".join(flags)}. '
                    f'Contact the President or an Administrator if you believe you should have access.'
                )
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def can_manage_roles(user):
    """Only the President or a superuser may edit role permissions."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    leader = getattr(user, 'leader_role', None)
    if not leader:
        return False
    # The 'can_manage_leaders' flag is what unlocks role admin.
    perms = getattr(leader, 'permissions', None)
    return bool(perms and perms.can_manage_leaders)
