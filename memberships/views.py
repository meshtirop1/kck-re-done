import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import SiteSettings
from .forms import BankSettingsForm, BenefitForm, DeclarePaymentForm, TierForm, VerifyForm
from .models import Membership, MembershipBenefit, MembershipPayment, MembershipTier, MembershipAuditLog
from .pdf import render_member_card_pdf
from .utils import (activate_membership, is_president_or_secretary, is_treasurer,
                    log_action, reject_membership)


# ---------- public / member-facing ----------

def membership_home(request):
    """Public marketing page: benefits, tier, how it works."""
    tier = MembershipTier.objects.filter(active=True).order_by('sort_order').first()
    benefits = MembershipBenefit.objects.filter(active=True)
    site = SiteSettings.load()

    current = None
    if request.user.is_authenticated:
        current = (Membership.objects.filter(user=request.user)
                   .order_by('-created_at').first())

    return render(request, 'memberships/home.html', {
        'tier': tier,
        'benefits': benefits,
        'site_settings': site,
        'current_membership': current,
    })


@login_required
def membership_apply(request):
    """Create a new Membership in PENDING_PAYMENT. One-click for existing users."""
    tier = MembershipTier.objects.filter(active=True).order_by('sort_order').first()
    if not tier:
        messages.error(request, 'Membership is not currently open. Please check back soon.')
        return redirect('memberships:home')

    # Prevent duplicate active/pending memberships
    existing = (Membership.objects.filter(user=request.user)
                .exclude(status__in=[Membership.STATUS_EXPIRED, Membership.STATUS_REJECTED])
                .first())
    if existing:
        return redirect('memberships:my_membership', pk=existing.pk)

    m = Membership.objects.create(
        user=request.user,
        tier=tier,
        expected_amount=tier.annual_amount,
        currency=tier.currency,
    )
    log_action(membership=m, actor=request.user, action='apply',
        description=f'Applied to tier {tier.name}', request=request,
        metadata={'amount': str(tier.annual_amount), 'currency': tier.currency})
    messages.success(request, 'Application started. Follow the bank transfer instructions below.')
    return redirect('memberships:my_membership', pk=m.pk)


@login_required
def my_membership(request, pk):
    m = get_object_or_404(Membership, pk=pk, user=request.user)
    site = SiteSettings.load()
    return render(request, 'memberships/my_membership.html', {
        'membership': m,
        'site_settings': site,
    })


@login_required
def declare_payment(request, pk):
    m = get_object_or_404(Membership, pk=pk, user=request.user)
    if m.status not in (Membership.STATUS_PENDING, Membership.STATUS_AWAITING):
        messages.warning(request, 'This membership is no longer awaiting payment.')
        return redirect('memberships:my_membership', pk=m.pk)

    if request.method == 'POST':
        form = DeclarePaymentForm(request.POST, request.FILES)
        if form.is_valid():
            pay = form.save(commit=False)
            pay.membership = m
            pay.save()
            m.status = Membership.STATUS_AWAITING
            m.payment_declared_at = timezone.now()
            m.save(update_fields=['status', 'payment_declared_at'])
            log_action(membership=m, actor=request.user, action='declare_payment',
                description=f'Declared {pay.claimed_amount} {m.currency} on {pay.claimed_date}',
                request=request,
                metadata={'claimed_amount': str(pay.claimed_amount),
                          'claimed_date': str(pay.claimed_date)})
            messages.success(request,
                'Thanks! Your payment is now awaiting treasurer verification.')
            return redirect('memberships:my_membership', pk=m.pk)
    else:
        form = DeclarePaymentForm(initial={'claimed_amount': m.expected_amount})

    return render(request, 'memberships/declare_payment.html',
        {'membership': m, 'form': form})


@login_required
def member_card_pdf(request, pk):
    m = get_object_or_404(Membership, pk=pk, user=request.user)
    if not m.is_active:
        messages.warning(request, 'Only active members can download the ID card.')
        return redirect('memberships:my_membership', pk=m.pk)
    buf = render_member_card_pdf(m, request=request)
    filename = f'KCK-Member-{m.member_number}.pdf'
    return FileResponse(buf, as_attachment=True, filename=filename, content_type='application/pdf')


def verify_membership(request, member_number):
    """Public page — QR code on the ID card scans here."""
    m = (Membership.objects
         .filter(member_number=member_number)
         .select_related('user', 'tier')
         .order_by('-period_end').first())
    valid = bool(m and m.is_active)
    return render(request, 'memberships/verify.html', {
        'membership': m,
        'member_number': member_number,
        'valid': valid,
    })


# ---------- treasurer dashboard ----------

def _treasurer_required(view):
    """Require login; authenticated non-treasurers get 403 (not a login redirect loop)."""
    from functools import wraps
    from django.core.exceptions import PermissionDenied

    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not is_treasurer(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@_treasurer_required
def treasurer_dashboard(request):
    today = timezone.now().date()
    stats = {
        'awaiting': Membership.objects.filter(status=Membership.STATUS_AWAITING).count(),
        'active': Membership.objects.filter(status=Membership.STATUS_ACTIVE,
            period_end__gte=today).count(),
        'pending': Membership.objects.filter(status=Membership.STATUS_PENDING).count(),
        'rejected': Membership.objects.filter(status=Membership.STATUS_REJECTED).count(),
        'expiring_30d': Membership.objects.filter(status=Membership.STATUS_ACTIVE,
            period_end__gte=today,
            period_end__lte=today + timezone.timedelta(days=30)).count(),
        'total_collected': (Membership.objects.filter(status=Membership.STATUS_ACTIVE)
                            .aggregate(s=Sum('expected_amount'))['s'] or 0),
    }
    queue = (Membership.objects.filter(status=Membership.STATUS_AWAITING)
             .select_related('user', 'tier').order_by('payment_declared_at')[:30])
    recent_verified = (Membership.objects.filter(status=Membership.STATUS_ACTIVE)
                       .select_related('user', 'verified_by')
                       .order_by('-activated_at')[:10])
    recent_logs = (MembershipAuditLog.objects.select_related('actor', 'membership__user')
                   .order_by('-created_at')[:15])
    return render(request, 'memberships/treasurer/dashboard.html', {
        'stats': stats,
        'queue': queue,
        'recent_verified': recent_verified,
        'recent_logs': recent_logs,
    })


@_treasurer_required
def treasurer_queue(request):
    status = request.GET.get('status', 'awaiting_verification')
    q = request.GET.get('q', '').strip()
    qs = Membership.objects.select_related('user', 'tier').order_by('-created_at')
    if status and status != 'all':
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(reference_code__icontains=q) |
                       Q(user__email__icontains=q) |
                       Q(user__username__icontains=q) |
                       Q(member_number__icontains=q))
    page_obj = Paginator(qs, 30).get_page(request.GET.get('page'))
    return render(request, 'memberships/treasurer/queue.html', {
        'page_obj': page_obj,
        'status': status,
        'q': q,
    })


@_treasurer_required
def treasurer_detail(request, pk):
    m = get_object_or_404(Membership.objects.select_related('user', 'tier', 'verified_by'), pk=pk)
    payments = m.payments.order_by('-created_at')
    logs = m.logs.select_related('actor').order_by('-created_at')

    if request.method == 'POST':
        form = VerifyForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['notes']
            if action == 'verify':
                activate_membership(m, verifier=request.user, request=request, notes=notes)
                messages.success(request, f'Membership verified. Member number {m.member_number} assigned.')
            else:
                reason = notes or 'No reason given'
                reject_membership(m, verifier=request.user, reason=reason, request=request)
                messages.info(request, 'Membership rejected.')
            return redirect('memberships:treasurer_detail', pk=m.pk)
    else:
        form = VerifyForm()

    site = SiteSettings.load()
    return render(request, 'memberships/treasurer/detail.html', {
        'membership': m,
        'payments': payments,
        'logs': logs,
        'form': form,
        'site_settings': site,
    })


@_treasurer_required
def treasurer_audit_log(request):
    qs = MembershipAuditLog.objects.select_related('actor', 'membership__user').order_by('-created_at')
    action = request.GET.get('action', '')
    if action:
        qs = qs.filter(action=action)
    page_obj = Paginator(qs, 50).get_page(request.GET.get('page'))
    return render(request, 'memberships/treasurer/audit_log.html', {
        'page_obj': page_obj,
        'action': action,
        'action_choices': MembershipAuditLog.ACTION_CHOICES,
    })


@_treasurer_required
def treasurer_tier(request):
    tier = MembershipTier.objects.filter(active=True).order_by('sort_order').first()
    if request.method == 'POST':
        form = TierForm(request.POST, instance=tier)
        if form.is_valid():
            old_amount = tier.annual_amount if tier else None
            new_tier = form.save()
            log_action(actor=request.user, action='tier_edit',
                description=f'Tier "{new_tier.name}" set to {new_tier.currency} {new_tier.annual_amount:,.0f}',
                request=request,
                metadata={'old_amount': str(old_amount) if old_amount else None,
                          'new_amount': str(new_tier.annual_amount)})
            messages.success(request, 'Membership tier updated.')
            return redirect('memberships:treasurer_tier')
    else:
        form = TierForm(instance=tier)
    return render(request, 'memberships/treasurer/tier.html', {'form': form, 'tier': tier})


@_treasurer_required
def treasurer_bank_settings(request):
    site = SiteSettings.load()
    initial = {k: getattr(site, k, '') for k in BankSettingsForm.base_fields}
    if request.method == 'POST':
        form = BankSettingsForm(request.POST)
        if form.is_valid():
            changes = []
            for k, v in form.cleaned_data.items():
                if getattr(site, k, '') != v:
                    changes.append(k)
                    setattr(site, k, v)
            site.save()
            log_action(actor=request.user, action='bank_edit',
                description=f'Updated fields: {", ".join(changes) if changes else "(no changes)"}',
                request=request, metadata={'fields_changed': changes})
            messages.success(request, 'Bank & membership settings updated.')
            return redirect('memberships:treasurer_bank')
    else:
        form = BankSettingsForm(initial=initial)
    return render(request, 'memberships/treasurer/bank_settings.html',
        {'form': form, 'site_settings': site})


@_treasurer_required
def treasurer_benefits(request):
    benefits = MembershipBenefit.objects.all().order_by('sort_order', 'id')
    return render(request, 'memberships/treasurer/benefits.html', {'benefits': benefits})


@_treasurer_required
def treasurer_benefit_edit(request, pk=None):
    benefit = get_object_or_404(MembershipBenefit, pk=pk) if pk else None
    if request.method == 'POST':
        form = BenefitForm(request.POST, instance=benefit)
        if form.is_valid():
            b = form.save()
            log_action(actor=request.user, action='benefit_edit',
                description=f'{"Updated" if pk else "Created"} benefit "{b.title}"',
                request=request)
            messages.success(request, 'Benefit saved.')
            return redirect('memberships:treasurer_benefits')
    else:
        form = BenefitForm(instance=benefit)
    return render(request, 'memberships/treasurer/benefit_edit.html',
        {'form': form, 'benefit': benefit})


@_treasurer_required
def treasurer_benefit_delete(request, pk):
    b = get_object_or_404(MembershipBenefit, pk=pk)
    if request.method == 'POST':
        title = b.title
        b.delete()
        log_action(actor=request.user, action='benefit_edit',
            description=f'Deleted benefit "{title}"', request=request)
        messages.success(request, 'Benefit deleted.')
        return redirect('memberships:treasurer_benefits')
    return render(request, 'memberships/treasurer/benefit_delete.html', {'benefit': b})


@_treasurer_required
def treasurer_bank_import(request):
    """Upload a CSV of bank transactions; auto-match by reference code.

    Accepted columns (case-insensitive, flexible): date, amount, description
    (or "details", "memo", "narration"). Shows a preview table with proposed
    matches; user confirms each. No DB changes until the user submits.
    """
    preview = None
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'preview':
            f = request.FILES.get('csv_file')
            if not f:
                messages.error(request, 'Please choose a CSV file to upload.')
            else:
                try:
                    text = f.read().decode('utf-8-sig', errors='replace')
                    reader = csv.DictReader(io.StringIO(text))
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= 500:
                            break
                        lower = {(k or '').strip().lower(): (v or '').strip() for k, v in row.items()}
                        desc = (lower.get('description') or lower.get('details')
                                or lower.get('memo') or lower.get('narration') or '')
                        amount = (lower.get('amount') or lower.get('credit')
                                  or lower.get('deposit') or lower.get('value') or '')
                        date = (lower.get('date') or lower.get('txn_date')
                                or lower.get('transaction_date') or '')

                        # find KCK-M-YYYY-XXXXXX reference in description
                        import re
                        m_ref = None
                        ref_match = re.search(r'KCK-M-\d{4}-[A-Z0-9]{6}', desc.upper())
                        if ref_match:
                            code = ref_match.group(0)
                            m_ref = Membership.objects.filter(reference_code=code).first()

                        rows.append({
                            'idx': i,
                            'desc': desc,
                            'amount': amount,
                            'date': date,
                            'match': m_ref,
                            'amount_ok': (m_ref and _amount_matches(amount, m_ref.expected_amount)) if m_ref else False,
                        })
                    preview = rows
                except Exception as e:
                    messages.error(request, f'Could not parse CSV: {e}')

        elif action == 'confirm':
            ids_to_verify = request.POST.getlist('verify_membership')
            count = 0
            for mid in ids_to_verify:
                try:
                    m = Membership.objects.get(pk=int(mid))
                    if m.status != Membership.STATUS_ACTIVE:
                        activate_membership(m, verifier=request.user, request=request,
                            notes='Auto-verified via bank CSV import')
                        count += 1
                except (Membership.DoesNotExist, ValueError):
                    pass
            log_action(actor=request.user, action='verify',
                description=f'Bulk CSV import: verified {count} memberships',
                request=request, metadata={'count': count})
            messages.success(request, f'Verified & activated {count} memberships from CSV.')
            return redirect('memberships:treasurer_bank_import')

    return render(request, 'memberships/treasurer/bank_import.html', {'preview': preview})


# ---------- President / oversight (read-only) ----------

def _oversight_required(view):
    """Require login; authenticated users who fail the test get 403, not a redirect loop."""
    from functools import wraps
    from django.core.exceptions import PermissionDenied

    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not is_president_or_secretary(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@_oversight_required
def oversight_dashboard(request):
    today = timezone.now().date()
    stats = {
        'active': Membership.objects.filter(status=Membership.STATUS_ACTIVE, period_end__gte=today).count(),
        'awaiting': Membership.objects.filter(status=Membership.STATUS_AWAITING).count(),
        'pending': Membership.objects.filter(status=Membership.STATUS_PENDING).count(),
        'expired': Membership.objects.filter(status=Membership.STATUS_EXPIRED).count(),
        'rejected': Membership.objects.filter(status=Membership.STATUS_REJECTED).count(),
        'total_collected': (Membership.objects.filter(status=Membership.STATUS_ACTIVE)
                            .aggregate(s=Sum('expected_amount'))['s'] or 0),
        'total_lifetime': (Membership.objects.exclude(status__in=[Membership.STATUS_PENDING, Membership.STATUS_REJECTED])
                           .aggregate(s=Sum('expected_amount'))['s'] or 0),
    }
    # Action breakdown (audit heatmap)
    from django.db.models import Count
    action_counts = (MembershipAuditLog.objects
                     .values('action')
                     .annotate(n=Count('id')).order_by('-n'))
    # Top actors (who's doing the verifications)
    top_actors = (MembershipAuditLog.objects.filter(actor__isnull=False)
                  .values('actor__username', 'actor__first_name', 'actor__last_name')
                  .annotate(n=Count('id')).order_by('-n')[:10])
    # Recent activations
    recent_verified = (Membership.objects.filter(status=Membership.STATUS_ACTIVE)
                       .select_related('user', 'verified_by')
                       .order_by('-activated_at')[:10])

    return render(request, 'memberships/oversight/dashboard.html', {
        'stats': stats,
        'action_counts': action_counts,
        'top_actors': top_actors,
        'recent_verified': recent_verified,
    })


@_oversight_required
def oversight_audit_log(request):
    qs = MembershipAuditLog.objects.select_related('actor', 'membership__user').order_by('-created_at')
    action = request.GET.get('action', '')
    actor = request.GET.get('actor', '').strip()
    if action:
        qs = qs.filter(action=action)
    if actor:
        qs = qs.filter(Q(actor__username__icontains=actor) |
                       Q(actor__email__icontains=actor) |
                       Q(actor__first_name__icontains=actor) |
                       Q(actor__last_name__icontains=actor))
    page_obj = Paginator(qs, 50).get_page(request.GET.get('page'))
    return render(request, 'memberships/oversight/audit_log.html', {
        'page_obj': page_obj,
        'action': action,
        'actor': actor,
        'action_choices': MembershipAuditLog.ACTION_CHOICES,
    })


@_oversight_required
def oversight_members(request):
    """Paginated list of all active members (read-only)."""
    today = timezone.now().date()
    qs = (Membership.objects.filter(status=Membership.STATUS_ACTIVE, period_end__gte=today)
          .select_related('user', 'tier').order_by('member_number'))
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(member_number__icontains=q) |
                       Q(user__username__icontains=q) |
                       Q(user__email__icontains=q) |
                       Q(user__first_name__icontains=q) |
                       Q(user__last_name__icontains=q))
    page_obj = Paginator(qs, 50).get_page(request.GET.get('page'))
    return render(request, 'memberships/oversight/members.html', {
        'page_obj': page_obj, 'q': q,
    })


@_oversight_required
def oversight_export_csv(request):
    """Download active-membership list as CSV."""
    today = timezone.now().date()
    qs = (Membership.objects.filter(status=Membership.STATUS_ACTIVE, period_end__gte=today)
          .select_related('user', 'tier').order_by('member_number'))
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="kck-active-members-{today}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Member Number', 'Name', 'Email', 'Tier', 'Amount', 'Valid From', 'Valid Until', 'Reference'])
    for m in qs:
        writer.writerow([
            m.member_number,
            m.user.get_full_name() or m.user.username,
            m.user.email,
            m.tier.name,
            f'{m.currency} {m.expected_amount}',
            m.period_start, m.period_end, m.reference_code,
        ])
    log_action(actor=request.user, action='tier_edit',
        description=f'Exported active members CSV ({qs.count()} rows)',
        request=request, metadata={'export_type': 'active_members_csv'})
    return response


def _amount_matches(csv_amount_str, expected):
    """True if the amount in the CSV (string) equals expected (Decimal)."""
    try:
        cleaned = ''.join(ch for ch in csv_amount_str if ch.isdigit() or ch in '.-')
        if not cleaned:
            return False
        from decimal import Decimal
        return Decimal(cleaned) == Decimal(str(expected))
    except Exception:
        return False
