"""Shared helpers for memberships: audit logging, permissions, activation."""
from datetime import timedelta
from django.core.mail import send_mail
from django.utils import timezone
from .models import Membership, MembershipAuditLog


def _client_ip(request):
    if not request:
        return None
    xf = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xf:
        return xf.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(*, membership=None, actor=None, action, description='', request=None, metadata=None):
    """Create an immutable audit log entry. Call from views/signals."""
    return MembershipAuditLog.objects.create(
        membership=membership,
        actor=actor,
        action=action,
        description=description,
        ip_address=_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''),
        metadata=metadata or {},
    )


def is_treasurer(user):
    """Anyone with `can_manage_memberships` permission (defaults to treasurers)."""
    from leaders.permissions import user_has_perm
    return user_has_perm(user, 'can_manage_memberships')


def is_president_or_secretary(user):
    """Read-only oversight access — anyone with `can_view_audit_log` permission
    (defaults to president, vice_president, secretary, treasurer)."""
    from leaders.permissions import user_has_perm
    return user_has_perm(user, 'can_view_audit_log')


def user_active_membership(user):
    """Return the user's current active Membership, or None."""
    if not user or not user.is_authenticated:
        return None
    from .models import Membership
    today = timezone.now().date()
    return (Membership.objects.filter(
                user=user, status=Membership.STATUS_ACTIVE, period_end__gte=today)
            .select_related('tier').first())


def membership_required(view_func):
    """Decorator: 403/redirect if the user doesn't have an active membership."""
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib import messages

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not user_active_membership(request.user):
            messages.info(request, 'This area is for KCK members. Become a member to access it.')
            return redirect('memberships:home')
        return view_func(request, *args, **kwargs)
    return _wrapped


def next_member_number():
    """Generate the next KCK-YYYY-NNNNN number. Padded, monotonically increasing."""
    year = timezone.now().year
    prefix = f'KCK-{year}-'
    existing = (Membership.objects
                .filter(member_number__startswith=prefix)
                .order_by('-member_number')
                .values_list('member_number', flat=True)
                .first())
    if existing:
        try:
            n = int(existing.split('-')[-1]) + 1
        except (ValueError, IndexError):
            n = 1
    else:
        n = 1
    return f'{prefix}{n:05d}'


def activate_membership(membership, verifier, request=None, notes=''):
    """Verify & activate a pending membership. Idempotent; safe to call once."""
    if membership.status == Membership.STATUS_ACTIVE:
        return membership

    now = timezone.now()
    # Assign member number if this is their first activation ever.
    if not membership.member_number:
        # Re-use existing number if user already has one (e.g. renewing)
        prior = (Membership.objects
                 .filter(user=membership.user, member_number__isnull=False)
                 .exclude(pk=membership.pk)
                 .exclude(member_number='')
                 .first())
        if prior:
            membership.member_number = prior.member_number
        else:
            membership.member_number = next_member_number()
            log_action(membership=membership, actor=verifier, action='member_number_assigned',
                description=f'Assigned member number {membership.member_number}', request=request)

    membership.status = Membership.STATUS_ACTIVE
    membership.activated_at = now
    membership.period_start = now.date()
    membership.period_end = (now + timedelta(days=365)).date()
    membership.verified_by = verifier
    if notes:
        membership.verification_notes = notes
    membership.save()

    log_action(membership=membership, actor=verifier, action='verify',
        description=f'Activated for period {membership.period_start} → {membership.period_end}',
        request=request,
        metadata={'amount': str(membership.expected_amount), 'currency': membership.currency})

    # Notify the member
    try:
        from core.models import SiteSettings
        site = SiteSettings.load()
        from_email = site.email or 'noreply@kenyakorea.com'
        if membership.user.email:
            send_mail(
                subject='[KCK] Your membership is now active',
                message=(
                    f'Hi {membership.user.get_full_name() or membership.user.username},\n\n'
                    f'Welcome — your KCK membership is active!\n\n'
                    f'Member number:  {membership.member_number}\n'
                    f'Valid:          {membership.period_start} → {membership.period_end}\n\n'
                    f'Download your ID card from the membership page on kenyakorea.com.\n\n'
                    f'SOTE PAMOJA — All Together\n'
                    f'Kenya Community in Korea'
                ),
                from_email=from_email,
                recipient_list=[membership.user.email],
                fail_silently=True,
            )
    except Exception:
        pass
    return membership


def reject_membership(membership, verifier, reason, request=None):
    membership.status = Membership.STATUS_REJECTED
    membership.rejection_reason = reason
    membership.verified_by = verifier
    membership.save()
    log_action(membership=membership, actor=verifier, action='reject',
        description=reason[:400], request=request)
    return membership
