from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic import TemplateView, FormView, ListView
from django.template.loader import render_to_string
from django.db.models import Q
from .forms import ContactForm, SearchForm
from .models import ContactMessage, AmbassadorProfile
from services.models import VisaType, Faq
from events_app.models import Event
from community.models import News, Testimonial
from leaders.models import Leader
from communications.models import Communication, Announcement as CommAnnouncement
from django.utils import timezone

def home(request):
    """Homepage with dynamic content."""
    president_msg = (Leader.objects
        .filter(is_active=True, show_message_on_home=True)
        .exclude(message='')
        .select_related('user')
        .order_by('sort_order').first())
    context = {
        'visa_types': VisaType.objects.filter(active=True)[:6],
        'upcoming_events': Event.objects.filter(active=True, date__gte=timezone.now()).order_by('date')[:3],
        'latest_news': News.objects.filter(published=True)[:3],
        'testimonials': Testimonial.objects.filter(active=True)[:6],
        'featured_news': News.objects.filter(published=True, featured=True).first(),
        'featured_leaders': Leader.objects.filter(is_active=True).order_by('sort_order')[:4],
        'latest_communications': Communication.objects.filter(status='published', audience='all').order_by('-published_at')[:3],
        'latest_announcements': CommAnnouncement.objects.filter(is_published=True).order_by('-published_at')[:4],
        'president_message': president_msg,
    }
    return render(request, 'pages/home.html', context)


def presidents_message(request):
    """Dedicated page showing the President's full message."""
    from django.shortcuts import get_object_or_404
    president = (Leader.objects
        .filter(role='president', is_active=True)
        .select_related('user').first())
    if not president:
        # Fall back to any leader with a featured message
        president = (Leader.objects
            .filter(is_active=True, show_message_on_home=True)
            .exclude(message='')
            .select_related('user').first())
    return render(request, 'pages/presidents_message.html', {
        'president': president,
    })

def about(request):
    ambassador = AmbassadorProfile.objects.filter(active=True).first()
    return render(request, 'pages/about.html', {'ambassador': ambassador})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            if request.user.is_authenticated:
                msg.user = request.user
            msg.save()
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('core:contact')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {'name': request.user.get_full_name() or request.user.username, 'email': request.user.email}
        form = ContactForm(initial=initial)
    return render(request, 'pages/contact.html', {'form': form})

def ambassador_profile(request):
    ambassador = AmbassadorProfile.objects.filter(active=True).first()
    return render(request, 'pages/ambassador.html', {'ambassador': ambassador})

def embassy_history(request):
    return render(request, 'pages/embassy_history.html')

def visit_us(request):
    return render(request, 'pages/visit.html')

def discover_kenya(request):
    from community.models import DiscoverAttraction, TravelEssential
    ctx = {
        'attractions': DiscoverAttraction.objects.filter(active=True),
        'essentials': TravelEssential.objects.filter(active=True),
    }
    return render(request, 'pages/discover.html', ctx)


def attraction_detail(request, slug):
    from django.shortcuts import get_object_or_404
    from community.models import DiscoverAttraction
    attraction = get_object_or_404(DiscoverAttraction, slug=slug, active=True)
    related = DiscoverAttraction.objects.filter(active=True).exclude(pk=attraction.pk)[:3]
    return render(request, 'pages/attraction_detail.html', {
        'attraction': attraction,
        'related': related,
    })

def search(request):
    query = request.GET.get('q', '').strip()
    results = {'visa_types': [], 'events': [], 'news': [], 'faqs': []}
    if query:
        results['visa_types'] = VisaType.objects.filter(Q(name__icontains=query) | Q(description__icontains=query), active=True)
        results['events'] = Event.objects.filter(Q(title__icontains=query) | Q(description__icontains=query), active=True)
        results['news'] = News.objects.filter(Q(title__icontains=query) | Q(content__icontains=query), published=True)
        results['faqs'] = Faq.objects.filter(Q(question__icontains=query) | Q(answer__icontains=query), active=True)
    return render(request, 'pages/search.html', {'query': query, 'results': results})

def newsletter_subscribe(request):
    from accounts.forms import NewsletterForm
    from accounts.models import NewsletterSubscription
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            obj, created = NewsletterSubscription.objects.get_or_create(email=email, defaults={'active': True})
            if created:
                messages.success(request, 'Thank you for subscribing to our newsletter!')
            else:
                messages.info(request, 'You are already subscribed.')
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))

class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'

class TermsView(TemplateView):
    template_name = 'pages/terms.html'

class DataHandlingView(TemplateView):
    template_name = 'pages/data_handling.html'


# ---------- Custom error handlers ----------

def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    # Explicitly render with a minimal context — context processors may fail during 500.
    try:
        return render(request, '500.html', status=500)
    except Exception:
        html = render_to_string('500.html')
        return HttpResponse(html, status=500)


def custom_403(request, exception=None):
    return render(request, '403.html', status=403)


def custom_400(request, exception=None):
    return render(request, '400.html', status=400)


def custom_csrf_failure(request, reason=''):
    return render(request, 'csrf_failure.html', status=403)
