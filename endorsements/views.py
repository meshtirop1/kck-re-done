from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404, FileResponse
from django.views.decorators.http import require_POST
from .models import Endorsement
from .forms import EndorsementForm, QuickEndorsementFromRequestForm
from .services import issue_endorsement


def _can_endorse(user):
    from leaders.permissions import user_has_perm
    return user_has_perm(user, 'can_review_endorsements')


def verify_home(request):
    endorsement = None
    searched = False
    code = request.GET.get('code', '').strip()
    if code:
        searched = True
        import uuid as _uuid
        try:
            _uuid.UUID(code)
            endorsement = Endorsement.objects.filter(verification_code=code).first()
        except (ValueError, TypeError):
            endorsement = None
        if not endorsement:
            endorsement = Endorsement.objects.filter(reference_number__iexact=code).first()
    return render(request, 'endorsements/verify_home.html', {
        'endorsement': endorsement, 'searched': searched, 'code': code,
    })


def verify(request, code):
    endorsement = get_object_or_404(Endorsement, verification_code=code)
    return render(request, 'endorsements/verify_detail.html', {'endorsement': endorsement})


@login_required
def my_endorsements(request):
    endorsements = request.user.endorsements_received.filter(status='issued')
    return render(request, 'endorsements/my_endorsements.html', {'endorsements': endorsements})


@login_required
def detail(request, pk):
    e = get_object_or_404(Endorsement, pk=pk)
    if e.user != request.user and not _can_endorse(request.user):
        raise Http404()
    return render(request, 'endorsements/detail.html', {'endorsement': e})


def download(request, pk):
    e = get_object_or_404(Endorsement, pk=pk, status='issued')
    if request.user.is_authenticated and (e.user == request.user or _can_endorse(request.user)):
        pass
    else:
        raise Http404()
    if not e.pdf_file:
        messages.error(request, 'PDF not yet generated.')
        return redirect('endorsements:detail', pk=pk)
    return FileResponse(e.pdf_file.open('rb'), as_attachment=True,
                        filename=f'{e.reference_number}.pdf')


@login_required
@user_passes_test(_can_endorse)
def manage_list(request):
    endorsements = Endorsement.objects.all().select_related('user', 'issued_by__user', 'related_service_request')
    status = request.GET.get('status')
    if status:
        endorsements = endorsements.filter(status=status)
    return render(request, 'endorsements/manage_list.html', {
        'endorsements': endorsements[:200],
        'total': endorsements.count(), 'status_filter': status,
    })


@login_required
@user_passes_test(_can_endorse)
def create(request):
    if request.method == 'POST':
        form = EndorsementForm(request.POST)
        if form.is_valid():
            e = form.save(commit=False)
            e.created_by = request.user
            if e.user and not e.member_full_name:
                e.member_full_name = e.user.get_full_name() or e.user.username
            e.save()
            messages.success(request,
                f'Endorsement {e.reference_number} saved as draft. Click Publish to generate the PDF.')
            return redirect('endorsements:manage_detail', pk=e.pk)
    else:
        form = EndorsementForm()
    return render(request, 'endorsements/create.html', {'form': form})


@login_required
@user_passes_test(_can_endorse)
def create_from_request(request, request_id):
    """Quick-generate an endorsement from an embassy service request."""
    from embassy_liaison.models import EmbassyServiceRequest
    svc_req = get_object_or_404(EmbassyServiceRequest, pk=request_id)

    if request.method == 'POST':
        quick_form = QuickEndorsementFromRequestForm(request.POST)
        if quick_form.is_valid():
            e = Endorsement.objects.create(
                user=svc_req.user,
                member_full_name=svc_req.full_name,
                member_id_number=svc_req.kenyan_id_number,
                endorsement_type=quick_form.cleaned_data['endorsement_type'],
                subject=quick_form.cleaned_data['subject'],
                addressed_to=quick_form.cleaned_data.get('addressed_to') or 'The Ambassador, Kenyan Embassy in Seoul',
                purpose=f'Accompanying service request {svc_req.request_number} ({svc_req.get_service_type_display()})',
                body=quick_form.cleaned_data['body'],
                member_standing=f'{svc_req.full_name} is a registered member of the Kenya Community in Korea (KCK), currently residing in {svc_req.city or "South Korea"}.',
                related_service_request=svc_req,
                created_by=request.user,
            )
            try:
                if request.user.leader_profile.is_active:
                    e.issued_by = request.user.leader_profile
                    e.save()
            except Exception:
                pass
            messages.success(request, f'Endorsement {e.reference_number} created as draft.')
            return redirect('endorsements:manage_detail', pk=e.pk)
    else:
        subject_map = {
            'passport_new': 'Cover Note for New Passport Application',
            'passport_renewal': 'Cover Note for Passport Renewal Application',
            'passport_replacement': 'Cover Note for Passport Replacement Application',
            'emergency_travel': 'Cover Note for Emergency Travel Document Application',
            'national_id': 'Cover Note for National ID Application',
            'notarization': 'Letter of Introduction for Document Notarization',
            'consular_letter': 'Letter of Endorsement - Consular Matter',
        }
        default_subject = subject_map.get(svc_req.service_type,
            f'Cover Note for {svc_req.get_service_type_display()}')
        default_body = (
            f'This letter is to formally endorse and accompany the above-referenced service request submitted by '
            f'{svc_req.full_name} through the Kenya Community in Korea (KCK).\n\n'
            f'The applicant is a member of our community and has completed our verification process. '
            f'We kindly request that you extend the necessary assistance and process this application according to '
            f'established procedures.\n\n'
            f'For any clarifications, please contact the KCK Secretariat using the details on our letterhead.'
        )
        quick_form = QuickEndorsementFromRequestForm(initial={
            'subject': default_subject,
            'addressed_to': 'The Ambassador, Kenyan Embassy in Seoul',
            'body': default_body,
        })
    return render(request, 'endorsements/create_from_request.html', {
        'form': quick_form, 'svc_request': svc_req,
    })


@login_required
@user_passes_test(_can_endorse)
def manage_detail(request, pk):
    e = get_object_or_404(Endorsement, pk=pk)
    return render(request, 'endorsements/manage_detail.html', {'endorsement': e})


@login_required
@user_passes_test(_can_endorse)
def edit(request, pk):
    e = get_object_or_404(Endorsement, pk=pk)
    if e.status == 'issued':
        messages.warning(request, 'This endorsement is already issued. Revoke it first to edit.')
        return redirect('endorsements:manage_detail', pk=pk)
    if request.method == 'POST':
        form = EndorsementForm(request.POST, instance=e)
        if form.is_valid():
            form.save()
            messages.success(request, 'Endorsement updated.')
            return redirect('endorsements:manage_detail', pk=pk)
    else:
        form = EndorsementForm(instance=e)
    return render(request, 'endorsements/create.html', {'form': form, 'endorsement': e})


@login_required
@user_passes_test(_can_endorse)
@require_POST
def publish(request, pk):
    e = get_object_or_404(Endorsement, pk=pk)
    try:
        issue_endorsement(e, request=request)
        messages.success(request,
            f'Endorsement {e.reference_number} has been issued and PDF generated.')
    except Exception as exc:
        messages.error(request, f'Failed to generate PDF: {exc}')
    return redirect('endorsements:manage_detail', pk=pk)


@login_required
@user_passes_test(_can_endorse)
@require_POST
def revoke(request, pk):
    e = get_object_or_404(Endorsement, pk=pk)
    e.status = 'revoked'
    e.revoke_reason = request.POST.get('reason', '')
    e.save()
    messages.success(request, f'Endorsement {e.reference_number} has been revoked.')
    return redirect('endorsements:manage_detail', pk=pk)
