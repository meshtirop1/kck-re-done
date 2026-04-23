from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import Certificate
from .forms import CertificateForm, VerifyCertificateForm
from .services import issue_certificate


def _can_issue_cert(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_admin', False):
        return True
    try:
        return user.leader_profile.permissions.can_issue_certificates and user.leader_profile.is_active
    except Exception:
        return False


def _is_uuid(s):
    import uuid as _uuid
    try:
        _uuid.UUID(s)
        return True
    except Exception:
        return False


def certificate_verify_home(request):
    """Public landing page to verify certificates."""
    form = VerifyCertificateForm(request.GET or None)
    certificate = None
    searched = False
    if request.GET.get('code'):
        searched = True
        code = request.GET.get('code', '').strip()
        # Try by verification_code UUID first, then cert_number
        certificate = Certificate.objects.filter(verification_code=code).first() if _is_uuid(code) else None
        if not certificate:
            certificate = Certificate.objects.filter(cert_number__iexact=code).first()
    return render(request, 'certificates/verify_home.html', {
        'form': form, 'certificate': certificate, 'searched': searched,
    })


def certificate_verify(request, code):
    """Verify certificate by its UUID verification code."""
    certificate = get_object_or_404(Certificate, verification_code=code)
    return render(request, 'certificates/verify_detail.html', {'certificate': certificate})


@login_required
def my_certificates(request):
    """List certificates issued to the current user."""
    certificates = request.user.certificates_received.filter(status='published')
    return render(request, 'certificates/my_certificates.html', {'certificates': certificates})


@login_required
def certificate_detail(request, pk):
    cert = get_object_or_404(Certificate, pk=pk)
    if cert.recipient_user != request.user and not _can_issue_cert(request.user):
        from django.http import Http404
        raise Http404()
    return render(request, 'certificates/certificate_detail.html', {'certificate': cert})


def certificate_download(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, status='published')
    if not cert.pdf_file:
        messages.error(request, 'Certificate PDF not yet generated.')
        return redirect('certificates:detail', pk=pk)
    return FileResponse(cert.pdf_file.open('rb'), as_attachment=True, filename=f'{cert.cert_number}.pdf')


@login_required
@user_passes_test(_can_issue_cert)
def certificate_create(request):
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.created_by = request.user
            cert.save()
            messages.success(request, f'Certificate {cert.cert_number} created. You can now publish it.')
            return redirect('certificates:manage_detail', pk=cert.pk)
    else:
        form = CertificateForm()
    return render(request, 'certificates/certificate_create.html', {'form': form})


@login_required
@user_passes_test(_can_issue_cert)
def certificate_manage_list(request):
    certificates = Certificate.objects.all().select_related('recipient_user', 'issued_by__user')
    return render(request, 'certificates/manage_list.html', {'certificates': certificates})


@login_required
@user_passes_test(_can_issue_cert)
def certificate_manage_detail(request, pk):
    cert = get_object_or_404(Certificate, pk=pk)
    return render(request, 'certificates/manage_detail.html', {'certificate': cert})


@login_required
@user_passes_test(_can_issue_cert)
@require_POST
def certificate_publish(request, pk):
    cert = get_object_or_404(Certificate, pk=pk)
    try:
        issue_certificate(cert, request=request)
        messages.success(request, f'Certificate {cert.cert_number} published successfully.')
    except Exception as e:
        messages.error(request, f'Failed to generate certificate: {e}')
    return redirect('certificates:manage_detail', pk=pk)
