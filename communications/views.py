from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404, FileResponse
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import Communication, Announcement, CommunicationDelivery
from .forms import CommunicationForm, AnnouncementForm
from .services import publish_communication


def _can_send(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_admin', False):
        return True
    try:
        return user.leader_profile.permissions.can_send_communications and user.leader_profile.is_active
    except Exception:
        return False


# ---------------- Public views ----------------

def announcements_list(request):
    qs = Announcement.objects.filter(is_published=True)
    category = request.GET.get('category')
    q = request.GET.get('q')
    if category:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q))
    paginator = Paginator(qs, 9)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'communications/announcements_list.html', {
        'page_obj': page,
        'categories': Announcement.CATEGORY_CHOICES,
        'selected_category': category or '',
        'q': q or '',
    })


def announcement_detail(request, slug):
    announcement = get_object_or_404(Announcement, slug=slug, is_published=True)
    related = Announcement.objects.filter(is_published=True).exclude(pk=announcement.pk)[:4]
    return render(request, 'communications/announcement_detail.html', {
        'announcement': announcement,
        'related': related,
    })


def communications_public_list(request):
    qs = Communication.objects.filter(status='published', audience='all')
    category = request.GET.get('category')
    q = request.GET.get('q')
    if category:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(Q(subject__icontains=q) | Q(body__icontains=q) | Q(reference_number__icontains=q))
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get('page'))
    from .models import COMM_CATEGORY_CHOICES
    return render(request, 'communications/public_list.html', {
        'page_obj': page,
        'categories': COMM_CATEGORY_CHOICES,
        'selected_category': category or '',
        'q': q or '',
    })


def communication_detail(request, pk):
    comm = get_object_or_404(Communication, pk=pk, status='published')
    # Only public communications visible here; others require membership
    if comm.audience != 'all' and not request.user.is_authenticated:
        messages.warning(request, 'Please log in to view this communication.')
        return redirect('accounts:login')
    return render(request, 'communications/detail.html', {'communication': comm})


def communication_download(request, pk):
    comm = get_object_or_404(Communication, pk=pk, status='published')
    if comm.audience != 'all' and not request.user.is_authenticated:
        return redirect('accounts:login')
    if not comm.pdf_file:
        raise Http404('PDF not available')
    response = FileResponse(
        comm.pdf_file.open('rb'),
        as_attachment=True,
        filename=f'{comm.reference_number.replace("/", "-")}.pdf',
    )
    return response


# ---------------- Member views ----------------

@login_required
def my_inbox(request):
    deliveries = (
        CommunicationDelivery.objects
        .filter(user=request.user, communication__status='published')
        .select_related('communication')
        .order_by('-delivered_at')
    )
    # Also include everyone-audience communications
    public_comms = Communication.objects.filter(status='published', audience='all')
    paginator = Paginator(deliveries, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'communications/inbox.html', {
        'page_obj': page,
        'public_comms': public_comms[:10],
    })


# ---------------- Leader/admin management ----------------

@login_required
@user_passes_test(_can_send)
def manage_communications_list(request):
    qs = Communication.objects.all()
    status = request.GET.get('status')
    category = request.GET.get('category')
    q = request.GET.get('q')
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(Q(subject__icontains=q) | Q(reference_number__icontains=q))
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    from .models import COMM_CATEGORY_CHOICES, COMM_STATUS_CHOICES
    return render(request, 'communications/manage_list.html', {
        'page_obj': page,
        'categories': COMM_CATEGORY_CHOICES,
        'statuses': COMM_STATUS_CHOICES,
        'selected_status': status or '',
        'selected_category': category or '',
        'q': q or '',
    })


@login_required
@user_passes_test(_can_send)
def communication_create(request):
    if request.method == 'POST':
        form = CommunicationForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Communication {obj.reference_number} saved as draft.')
            return redirect('communications:manage_detail', pk=obj.pk)
    else:
        form = CommunicationForm()
    return render(request, 'communications/create.html', {'form': form, 'is_edit': False})


@login_required
@user_passes_test(_can_send)
def communication_edit(request, pk):
    comm = get_object_or_404(Communication, pk=pk)
    if request.method == 'POST':
        form = CommunicationForm(request.POST, request.FILES, instance=comm)
        if form.is_valid():
            form.save()
            messages.success(request, 'Communication updated.')
            return redirect('communications:manage_detail', pk=comm.pk)
    else:
        form = CommunicationForm(instance=comm)
    return render(request, 'communications/create.html', {
        'form': form,
        'is_edit': True,
        'communication': comm,
    })


@login_required
@user_passes_test(_can_send)
def manage_communication_detail(request, pk):
    comm = get_object_or_404(Communication, pk=pk)
    return render(request, 'communications/manage_detail.html', {'communication': comm})


@login_required
@user_passes_test(_can_send)
@require_POST
def communication_publish(request, pk):
    comm = get_object_or_404(Communication, pk=pk)
    try:
        publish_communication(comm, request=request)
        messages.success(request, f'Communication {comm.reference_number} published.')
    except Exception as exc:
        messages.error(request, f'Failed to publish: {exc}')
    return redirect('communications:manage_detail', pk=comm.pk)


@login_required
@user_passes_test(_can_send)
def manage_announcements_list(request):
    qs = Announcement.objects.all()
    q = request.GET.get('q')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(excerpt__icontains=q))
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'communications/manage_announcements.html', {
        'page_obj': page,
        'q': q or '',
    })


@login_required
@user_passes_test(_can_send)
def announcement_create(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            messages.success(request, 'Announcement saved.')
            return redirect('communications:manage_announcements')
    else:
        form = AnnouncementForm()
    return render(request, 'communications/announcement_create.html', {'form': form, 'is_edit': False})


@login_required
@user_passes_test(_can_send)
def announcement_edit(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=ann)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated.')
            return redirect('communications:manage_announcements')
    else:
        form = AnnouncementForm(instance=ann)
    return render(request, 'communications/announcement_create.html', {
        'form': form,
        'is_edit': True,
        'announcement': ann,
    })


@login_required
@user_passes_test(_can_send)
@require_POST
def announcement_publish(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    ann.is_published = not ann.is_published
    if ann.is_published and not ann.published_at:
        ann.published_at = timezone.now()
    ann.save()
    messages.success(
        request,
        'Announcement published.' if ann.is_published else 'Announcement unpublished.'
    )
    return redirect('communications:manage_announcements')
