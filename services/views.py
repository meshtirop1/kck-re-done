from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .models import VisaType, VisaApplication, PassportApplication, Faq


def visa_types(request):
    visa_types = VisaType.objects.filter(active=True)
    return render(request, 'services/visa_types.html', {'visa_types': visa_types})


def visa_type_detail(request, slug):
    visa_type = get_object_or_404(VisaType, slug=slug, active=True)
    return render(request, 'services/visa_type_detail.html', {'visa_type': visa_type, 'visa': visa_type})


def visa_services(request):
    visa_types = VisaType.objects.filter(active=True)
    return render(request, 'services/visa_services.html', {'visa_types': visa_types})


def visa_issues(request):
    return render(request, 'services/visa_issues.html')


def visa_faqs(request):
    faqs = Faq.objects.filter(active=True)
    grouped = {}
    for faq in faqs:
        grouped.setdefault(faq.get_category_display(), []).append(faq)
    return render(request, 'services/faqs.html', {'grouped_faqs': grouped})


# ---- Application endpoints REMOVED ----
# KCK is a community organisation, not the embassy. Visa & passport applications
# are processed by the Embassy of Kenya in Seoul, not by KCK. The "apply" URLs
# below now redirect to the visa type list (information) so any old bookmarks /
# in-page links continue to work without 500-ing.


def visa_apply(request):
    """Legacy URL — informational redirect."""
    messages.info(request,
        'KCK does not process visa applications. Below is the information you should '
        'prepare; for the actual application, please contact the Embassy of Kenya in Seoul.')
    return redirect('services:visa_types')


@login_required
def visa_application_detail(request, pk):
    """Legacy view — historical applications are still readable to their owner."""
    app = get_object_or_404(VisaApplication, pk=pk)
    if app.user != request.user and not getattr(request.user, 'is_admin', False):
        raise Http404()
    return render(request, 'services/visa_application_detail.html', {'application': app})


def passport_request(request):
    return render(request, 'services/passport_request.html')


def passport_apply(request):
    """Legacy URL — informational redirect."""
    messages.info(request,
        'KCK does not process passport applications. Below is the information you should '
        'prepare; for the actual application, please contact the Embassy of Kenya in Seoul.')
    return redirect('services:passport_request')


@login_required
def passport_application_detail(request, pk):
    """Legacy view — historical applications are still readable to their owner."""
    app = get_object_or_404(PassportApplication, pk=pk)
    if app.user != request.user and not getattr(request.user, 'is_admin', False):
        raise Http404()
    return render(request, 'services/passport_application_detail.html', {'application': app})


def queries(request):
    return render(request, 'services/queries.html')


def highlights(request):
    return render(request, 'services/highlights.html')


def all_faqs(request):
    faqs = Faq.objects.filter(active=True)
    grouped = {}
    for faq in faqs:
        grouped.setdefault(faq.get_category_display(), []).append(faq)
    return render(request, 'services/faqs.html', {'grouped_faqs': grouped})
