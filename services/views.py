from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .models import VisaType, VisaApplication, PassportApplication, Faq
from .forms import VisaApplicationForm, PassportApplicationForm

def visa_types(request):
    visa_types = VisaType.objects.filter(active=True)
    return render(request, 'services/visa_types.html', {'visa_types': visa_types})

def visa_type_detail(request, slug):
    visa_type = get_object_or_404(VisaType, slug=slug, active=True)
    # Pass both names for template compatibility
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

@login_required
def visa_apply(request):
    if request.method == 'POST':
        form = VisaApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.save()
            messages.success(request, 'Your visa application has been submitted successfully.')
            return redirect('services:visa_application_detail', pk=app.pk)
    else:
        form = VisaApplicationForm()
    return render(request, 'services/visa_apply.html', {'form': form})

@login_required
def visa_application_detail(request, pk):
    app = get_object_or_404(VisaApplication, pk=pk)
    if app.user != request.user and not request.user.is_admin:
        raise Http404()
    return render(request, 'services/visa_application_detail.html', {'application': app})

def passport_request(request):
    return render(request, 'services/passport_request.html')

@login_required
def passport_apply(request):
    if request.method == 'POST':
        form = PassportApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.save()
            messages.success(request, 'Your passport application has been submitted successfully.')
            return redirect('services:passport_application_detail', pk=app.pk)
    else:
        form = PassportApplicationForm(initial={'email': request.user.email, 'full_name': request.user.get_full_name()})
    return render(request, 'services/passport_apply.html', {'form': form})

@login_required
def passport_application_detail(request, pk):
    app = get_object_or_404(PassportApplication, pk=pk)
    if app.user != request.user and not request.user.is_admin:
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
