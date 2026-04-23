from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import Http404, FileResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from .models import EmbassyServiceRequest, RequestNote, ServiceGuide, SERVICE_TYPE_CHOICES
from .forms import EmbassyServiceRequestForm, RequestNoteForm, RequestStatusUpdateForm, AssignOfficerForm


def _is_officer(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_admin', False):
        return True
    try:
        return user.leader_profile.is_active
    except Exception:
        return False


def liaison_info(request):
    guides = ServiceGuide.objects.filter(active=True)
    return render(request, 'embassy_liaison/info.html', {'guides': guides})


def service_guide_list(request):
    guides = ServiceGuide.objects.filter(active=True)
    return render(request, 'embassy_liaison/service_list.html', {'guides': guides})


def service_guide_detail(request, service_type):
    guide = get_object_or_404(ServiceGuide, service_type=service_type, active=True)
    return render(request, 'embassy_liaison/service_detail.html', {'guide': guide})


@login_required
def request_create(request):
    if request.method == 'POST':
        form = EmbassyServiceRequestForm(request.POST, request.FILES)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            RequestNote.objects.create(
                request=req, author=request.user, note_type='system',
                message=f'Request submitted by {request.user.get_full_name() or request.user.username}.'
            )
            messages.success(request,
                f'Your request {req.request_number} has been submitted successfully. '
                'A KCK officer will review it and contact you shortly.')
            return redirect('embassy_liaison:my_request_detail', pk=req.pk)
    else:
        initial = {
            'full_name': request.user.get_full_name(),
            'phone': getattr(request.user, 'phone', ''),
            'korean_phone': getattr(request.user, 'korean_phone', ''),
            'city': getattr(request.user, 'city', ''),
            'address_in_korea': getattr(request.user, 'address_korea', ''),
        }
        if request.GET.get('service_type'):
            initial['service_type'] = request.GET.get('service_type')
        form = EmbassyServiceRequestForm(initial=initial)
    return render(request, 'embassy_liaison/request_create.html', {'form': form})


@login_required
def my_requests(request):
    qs = request.user.embassy_requests.all().order_by('-submitted_at')
    return render(request, 'embassy_liaison/my_requests.html', {'requests': qs})


@login_required
def my_request_detail(request, pk):
    req = get_object_or_404(EmbassyServiceRequest, pk=pk)
    if req.user != request.user and not _is_officer(request.user):
        raise Http404()

    note_form = RequestNoteForm()
    if request.method == 'POST' and 'add_note' in request.POST:
        note_form = RequestNoteForm(request.POST, request.FILES)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.request = req
            note.author = request.user
            note.note_type = 'officer_reply' if _is_officer(request.user) else 'member_message'
            note.save()
            messages.success(request, 'Your message has been sent.')
            return redirect('embassy_liaison:my_request_detail', pk=pk)

    if _is_officer(request.user):
        visible_notes = req.notes.all()
    else:
        visible_notes = req.notes.filter(is_internal=False)

    return render(request, 'embassy_liaison/request_detail.html', {
        'req': req,
        'request_obj': req,
        'notes': visible_notes,
        'note_form': note_form,
        'is_officer': _is_officer(request.user),
    })


@login_required
@require_POST
def request_cancel(request, pk):
    req = get_object_or_404(EmbassyServiceRequest, pk=pk, user=request.user)
    if req.status in ('completed', 'rejected', 'cancelled'):
        messages.error(request, 'This request cannot be cancelled.')
    else:
        req.status = 'cancelled'
        req.save()
        RequestNote.objects.create(
            request=req, author=request.user, note_type='status_change',
            message='Request cancelled by member.'
        )
        messages.success(request, 'Your request has been cancelled.')
    return redirect('embassy_liaison:my_request_detail', pk=pk)


@login_required
@user_passes_test(_is_officer)
def officer_dashboard(request):
    qs = EmbassyServiceRequest.objects.all()
    stats = {
        'total': qs.count(),
        'submitted': qs.filter(status='submitted').count(),
        'under_review': qs.filter(status='under_review').count(),
        'forwarded': qs.filter(status__in=['forwarded', 'embassy_processing']).count(),
        'completed': qs.filter(status='completed').count(),
        'urgent': qs.filter(priority__in=['urgent', 'emergency']).exclude(status__in=['completed', 'cancelled']).count(),
        'my_assigned': qs.filter(assigned_officer=request.user).exclude(status__in=['completed', 'cancelled']).count(),
    }
    recent = qs.order_by('-submitted_at')[:10]
    my_requests = qs.filter(assigned_officer=request.user).exclude(status__in=['completed', 'cancelled']).order_by('-submitted_at')[:10]
    urgent_requests = qs.filter(priority__in=['urgent', 'emergency']).exclude(status__in=['completed', 'cancelled']).order_by('-submitted_at')[:10]
    return render(request, 'embassy_liaison/officer_dashboard.html', {
        'stats': stats, 'recent': recent, 'my_requests': my_requests, 'urgent_requests': urgent_requests,
    })


@login_required
@user_passes_test(_is_officer)
def officer_request_list(request):
    qs = EmbassyServiceRequest.objects.all().select_related('user', 'assigned_officer')
    status = request.GET.get('status')
    service_type = request.GET.get('service_type')
    priority = request.GET.get('priority')
    assigned = request.GET.get('assigned')
    search = request.GET.get('q', '').strip()

    if status: qs = qs.filter(status=status)
    if service_type: qs = qs.filter(service_type=service_type)
    if priority: qs = qs.filter(priority=priority)
    if assigned == 'me': qs = qs.filter(assigned_officer=request.user)
    elif assigned == 'unassigned': qs = qs.filter(assigned_officer__isnull=True)
    if search:
        qs = qs.filter(
            Q(request_number__icontains=search) | Q(full_name__icontains=search) |
            Q(kenyan_id_number__icontains=search) | Q(user__email__icontains=search)
        )

    return render(request, 'embassy_liaison/officer_request_list.html', {
        'requests': qs[:100],
        'total': qs.count(),
        'filters': {'status': status, 'service_type': service_type, 'priority': priority, 'assigned': assigned, 'q': search},
        'service_type_choices': SERVICE_TYPE_CHOICES,
    })


@login_required
@user_passes_test(_is_officer)
def officer_request_detail(request, pk):
    req = get_object_or_404(EmbassyServiceRequest, pk=pk)
    status_form = RequestStatusUpdateForm(initial={'status': req.status, 'embassy_reference': req.embassy_reference})
    assign_form = AssignOfficerForm(initial={'officer': req.assigned_officer})
    note_form = RequestNoteForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            status_form = RequestStatusUpdateForm(request.POST)
            if status_form.is_valid():
                new_status = status_form.cleaned_data['status']
                old_status = req.status
                req.status = new_status
                if status_form.cleaned_data.get('embassy_reference'):
                    req.embassy_reference = status_form.cleaned_data['embassy_reference']
                if new_status == 'forwarded' and not req.forwarded_at:
                    req.forwarded_at = timezone.now()
                if new_status == 'completed' and not req.completed_at:
                    req.completed_at = timezone.now()
                req.save()

                note_msg = status_form.cleaned_data.get('message_to_member', '').strip()
                note_body = f'Status changed from "{old_status}" to "{new_status}".'
                if note_msg:
                    note_body += f'\n\nMessage: {note_msg}'
                RequestNote.objects.create(
                    request=req, author=request.user, note_type='status_change',
                    message=note_body, is_internal=False,
                )
                internal_note = status_form.cleaned_data.get('internal_note', '').strip()
                if internal_note:
                    RequestNote.objects.create(
                        request=req, author=request.user, note_type='officer_reply',
                        message=internal_note, is_internal=True,
                    )
                messages.success(request, 'Request status updated successfully.')
                return redirect('embassy_liaison:officer_request_detail', pk=pk)

        elif action == 'assign':
            assign_form = AssignOfficerForm(request.POST)
            if assign_form.is_valid():
                officer = assign_form.cleaned_data['officer']
                req.assigned_officer = officer
                req.save()
                RequestNote.objects.create(
                    request=req, author=request.user, note_type='system',
                    message=f'Request {"assigned to " + officer.get_full_name() if officer else "unassigned"}.',
                    is_internal=True,
                )
                messages.success(request, 'Officer assignment updated.')
                return redirect('embassy_liaison:officer_request_detail', pk=pk)

        elif action == 'add_note':
            note_form = RequestNoteForm(request.POST, request.FILES)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.request = req
                note.author = request.user
                note.note_type = 'officer_reply'
                note.is_internal = bool(request.POST.get('is_internal'))
                note.save()
                messages.success(request, 'Message added to the request.')
                return redirect('embassy_liaison:officer_request_detail', pk=pk)

    return render(request, 'embassy_liaison/officer_request_detail.html', {
        'req': req,
        'request_obj': req,
        'notes': req.notes.all(),
        'status_form': status_form,
        'assign_form': assign_form,
        'note_form': note_form,
    })


@login_required
def document_download(request, pk, doc):
    req = get_object_or_404(EmbassyServiceRequest, pk=pk)
    if req.user != request.user and not _is_officer(request.user):
        raise Http404()
    field_name = {'1': 'supporting_document_1', '2': 'supporting_document_2', '3': 'supporting_document_3'}.get(doc)
    if not field_name:
        raise Http404()
    file_field = getattr(req, field_name)
    if not file_field:
        raise Http404()
    return FileResponse(file_field.open('rb'), as_attachment=True)
