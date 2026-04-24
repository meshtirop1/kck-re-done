"""Admin/Leader Portal — integrated CRUD for all editable content.

Access: Admins (is_admin or superuser) OR active Leaders.
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q

# Models
from services.models import VisaType, Faq, VisaApplication, PassportApplication
from events_app.models import Event
from community.models import News, Testimonial, Announcement as SiteAnnouncement, Page, DiscoverAttraction, TravelEssential
from communications.models import Communication, Announcement as CommAnnouncement
from embassy_liaison.models import ServiceGuide, EmbassyServiceRequest
from certificates.models import Certificate
from leaders.models import Leader
from core.models import SiteSettings, ContactMessage
from accounts.models import NewsletterSubscription
from market.models import SellerProfile, Product, ProductCategory


def _is_portal_staff(user):
    """Anyone with at least one permission flag (or superuser/admin) can see the portal."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_admin', False):
        return True
    from leaders.permissions import user_perm_set
    return bool(user_perm_set(user))


def _portal_staff_required(view):
    """Decorator: login required + must be portal-eligible. Returns 403 (not redirect-loop) for blocked authenticated users."""
    from functools import wraps
    from django.core.exceptions import PermissionDenied

    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not _is_portal_staff(request.user):
            raise PermissionDenied('You do not have any portal permissions. Contact the President if you need access.')
        return view(request, *args, **kwargs)
    return wrapped


class PortalStaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = '/accounts/login/'
    raise_exception = True  # 403 instead of redirect loop
    def test_func(self):
        return _is_portal_staff(self.request.user)


# Map portal CRUD keys to the permission flag that gates them.
# Anything not listed is gated by the catch-all rule (must hold ANY permission).
PORTAL_KEY_PERMS = {
    'visa-types': 'can_manage_content',
    'service-guides': 'can_manage_content',
    'faqs': 'can_manage_content',
    'news': 'can_manage_content',
    'site-banners': 'can_manage_content',
    'testimonials': 'can_manage_content',
    'pages': 'can_manage_content',
    'discover-attractions': 'can_manage_content',
    'travel-essentials': 'can_manage_content',
    'announcements': 'can_send_communications',
    'events': 'can_manage_events',
    'leaders': 'can_manage_leaders',
}


def _require_portal_perm(request, key):
    """Raise 403 if the user lacks the right permission for a portal CRUD key."""
    from leaders.permissions import user_has_perm
    from django.core.exceptions import PermissionDenied
    flag = PORTAL_KEY_PERMS.get(key)
    if flag and not user_has_perm(request.user, flag):
        raise PermissionDenied(f'You need the "{flag}" permission to manage {key.replace("-", " ")}.')


@_portal_staff_required
def dashboard(request):
    stats = {
        'visa_types': VisaType.objects.count(),
        'visa_applications_pending': VisaApplication.objects.filter(status='pending').count(),
        'passport_applications_pending': PassportApplication.objects.filter(status='pending').count(),
        'embassy_requests_open': EmbassyServiceRequest.objects.exclude(status__in=['completed', 'cancelled', 'rejected']).count(),
        'events_upcoming': Event.objects.filter(active=True).count(),
        'faqs': Faq.objects.filter(active=True).count(),
        'news': News.objects.filter(published=True).count(),
        'announcements': CommAnnouncement.objects.filter(is_published=True).count(),
        'testimonials': Testimonial.objects.filter(active=True).count(),
        'service_guides': ServiceGuide.objects.filter(active=True).count(),
        'leaders': Leader.objects.filter(is_active=True).count(),
        'pages': Page.objects.filter(active=True).count(),
        'contact_messages_unread': ContactMessage.objects.filter(is_read=False).count(),
        'certificates': Certificate.objects.count(),
        'communications': Communication.objects.count(),
        'newsletter_subs': NewsletterSubscription.objects.filter(active=True).count(),
        # Market
        'market_sellers_pending': SellerProfile.objects.filter(status='pending').count(),
        'market_sellers_approved': SellerProfile.objects.filter(status='approved', active=True).count(),
        'market_products': Product.objects.filter(is_available=True, seller__status='approved').count(),
        'market_categories': ProductCategory.objects.filter(active=True).count(),
    }
    recent_contact = ContactMessage.objects.order_by('-created_at')[:5]
    recent_requests = EmbassyServiceRequest.objects.order_by('-submitted_at')[:5]
    return render(request, 'portal/dashboard.html', {
        'stats': stats,
        'recent_contact': recent_contact,
        'recent_requests': recent_requests,
    })


# Registry of manageable models
MANAGED_MODELS = {
    'visa-types': {
        'model': VisaType, 'name': 'Visa Type', 'name_plural': 'Visa Types', 'icon': '🛂',
        'fields': ['name', 'slug', 'description', 'requirements', 'processing_time', 'fee', 'icon', 'sort_order', 'active'],
        'list_fields': ['name', 'processing_time', 'sort_order', 'active'],
        'search_fields': ['name', 'description'],
    },
    'faqs': {
        'model': Faq, 'name': 'FAQ', 'name_plural': 'FAQs', 'icon': '❓',
        'fields': ['question', 'answer', 'category', 'sort_order', 'active'],
        'list_fields': ['question', 'category', 'sort_order', 'active'],
        'search_fields': ['question', 'answer'],
    },
    'events': {
        'model': Event, 'name': 'Event', 'name_plural': 'Events', 'icon': '📅',
        'fields': ['title', 'slug', 'description', 'date', 'end_date', 'location', 'image',
                   'capacity', 'registration_deadline', 'active', 'featured'],
        'list_fields': ['title', 'date', 'location', 'active', 'featured'],
        'search_fields': ['title', 'location'],
    },
    'news': {
        'model': News, 'name': 'News Article', 'name_plural': 'News Articles', 'icon': '📰',
        'fields': ['title', 'slug', 'excerpt', 'content', 'featured_image', 'published', 'featured'],
        'list_fields': ['title', 'published_at', 'published', 'featured'],
        'search_fields': ['title', 'excerpt', 'content'],
    },
    'announcements': {
        'model': CommAnnouncement, 'name': 'Announcement', 'name_plural': 'Announcements', 'icon': '📢',
        'fields': ['title', 'slug', 'excerpt', 'body', 'category', 'cover_image', 'is_published', 'is_pinned'],
        'list_fields': ['title', 'category', 'is_published', 'is_pinned'],
        'search_fields': ['title', 'body'],
    },
    'site-banners': {
        'model': SiteAnnouncement, 'name': 'Site Banner', 'name_plural': 'Site Banners (Top)', 'icon': '🔔',
        'fields': ['title', 'message', 'level', 'active', 'starts_at', 'ends_at'],
        'list_fields': ['title', 'level', 'active', 'starts_at', 'ends_at'],
        'search_fields': ['title', 'message'],
    },
    'testimonials': {
        'model': Testimonial, 'name': 'Testimonial', 'name_plural': 'Testimonials', 'icon': '💬',
        'fields': ['name', 'role', 'message', 'photo', 'active'],
        'list_fields': ['name', 'role', 'active'],
        'search_fields': ['name', 'message'],
    },
    'service-guides': {
        'model': ServiceGuide, 'name': 'Embassy Service Guide', 'name_plural': 'Embassy Service Guides', 'icon': '📋',
        'fields': ['service_type', 'title', 'description', 'requirements', 'typical_timeline',
                   'embassy_fee', 'kck_facilitation_fee', 'icon', 'additional_info', 'active', 'sort_order'],
        'list_fields': ['title', 'service_type', 'typical_timeline', 'active'],
        'search_fields': ['title', 'description'],
    },
    'leaders': {
        'model': Leader, 'name': 'Leader', 'name_plural': 'Leaders', 'icon': '👥',
        'fields': ['user', 'role', 'title', 'bio',
                   'message_title', 'message', 'show_message_on_home',
                   'photo', 'signature', 'stamp',
                   'email_official', 'phone_official', 'sort_order', 'is_active',
                   'appointed_at', 'term_ends'],
        'list_fields': ['user', 'role', 'title', 'is_active', 'sort_order'],
        'search_fields': ['title'],
    },
    'pages': {
        'model': Page, 'name': 'Content Page', 'name_plural': 'Content Pages', 'icon': '📄',
        'fields': ['slug', 'title', 'content', 'meta_description', 'featured_image', 'active'],
        'list_fields': ['title', 'slug', 'active', 'updated_at'],
        'search_fields': ['title', 'content'],
    },
    'discover-attractions': {
        'model': DiscoverAttraction, 'name': 'Discover Attraction', 'name_plural': 'Discover Kenya · Attractions', 'icon': '🌍',
        'fields': ['title', 'short_description', 'description', 'image', 'icon', 'sort_order', 'featured', 'active'],
        'list_fields': ['title', 'sort_order', 'featured', 'active'],
        'search_fields': ['title', 'short_description'],
    },
    'travel-essentials': {
        'model': TravelEssential, 'name': 'Travel Essential', 'name_plural': 'Discover Kenya · Travel Essentials', 'icon': '🧳',
        'fields': ['title', 'value', 'icon', 'sort_order', 'active'],
        'list_fields': ['title', 'value', 'sort_order', 'active'],
        'search_fields': ['title', 'value'],
    },
}


def _get_config(key):
    cfg = MANAGED_MODELS.get(key)
    if not cfg:
        from django.http import Http404
        raise Http404(f'No management config for "{key}"')
    return cfg


def _render_field_value(obj, field_name):
    try:
        val = getattr(obj, field_name)
    except AttributeError:
        return '—'
    if callable(val):
        try:
            val = val()
        except Exception:
            return '—'
    if val is None or val == '':
        return '—'
    if isinstance(val, bool):
        return '✓' if val else '✗'
    if hasattr(val, 'strftime'):
        try:
            return val.strftime('%Y-%m-%d')
        except Exception:
            return str(val)
    s = str(val)
    return s[:80] + '...' if len(s) > 80 else s


@_portal_staff_required
def generic_list(request, key):
    _require_portal_perm(request, key)
    cfg = _get_config(key)
    Model = cfg['model']
    qs = Model.objects.all()

    q = request.GET.get('q', '').strip()
    if q and cfg.get('search_fields'):
        filter_q = Q()
        for f in cfg['search_fields']:
            filter_q |= Q(**{f'{f}__icontains': q})
        qs = qs.filter(filter_q)

    rows = []
    for obj in qs[:200]:
        rows.append({
            'obj': obj,
            'pk': obj.pk,
            'cells': [_render_field_value(obj, f) for f in cfg['list_fields']],
            'str': str(obj),
        })

    return render(request, 'portal/generic_list.html', {
        'cfg': cfg, 'key': key, 'rows': rows, 'total': qs.count(), 'q': q,
    })


@_portal_staff_required
def generic_create(request, key):
    _require_portal_perm(request, key)
    cfg = _get_config(key)
    Model = cfg['model']
    FormClass = _form_class_for(Model, cfg['fields'])

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f'{cfg["name"]} "{obj}" created successfully.')
            return redirect('portal:list', key=key)
    else:
        form = FormClass()

    return render(request, 'portal/generic_form.html', {
        'cfg': cfg, 'key': key, 'form': form, 'action': 'Create',
    })


@_portal_staff_required
def generic_edit(request, key, pk):
    _require_portal_perm(request, key)
    cfg = _get_config(key)
    Model = cfg['model']
    obj = get_object_or_404(Model, pk=pk)
    FormClass = _form_class_for(Model, cfg['fields'])

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f'{cfg["name"]} "{obj}" updated successfully.')
            return redirect('portal:list', key=key)
    else:
        form = FormClass(instance=obj)

    return render(request, 'portal/generic_form.html', {
        'cfg': cfg, 'key': key, 'form': form, 'action': 'Edit', 'obj': obj,
    })


@_portal_staff_required
def generic_delete(request, key, pk):
    _require_portal_perm(request, key)
    cfg = _get_config(key)
    Model = cfg['model']
    obj = get_object_or_404(Model, pk=pk)

    if request.method == 'POST':
        name = str(obj)
        obj.delete()
        messages.success(request, f'{cfg["name"]} "{name}" deleted successfully.')
        return redirect('portal:list', key=key)

    return render(request, 'portal/generic_delete.html', {
        'cfg': cfg, 'key': key, 'obj': obj,
    })


@_portal_staff_required
def site_settings(request):
    from leaders.permissions import user_has_perm
    from django.core.exceptions import PermissionDenied
    if not user_has_perm(request.user, 'can_manage_settings'):
        raise PermissionDenied('You need the "can_manage_settings" permission.')
    from django import forms as djforms
    obj = SiteSettings.load()

    class SiteSettingsForm(djforms.ModelForm):
        class Meta:
            model = SiteSettings
            fields = [
                # Identity
                'site_name', 'site_short_name', 'tagline', 'logo',
                # Slogan
                'slogan', 'slogan_translation', 'slogan_description',
                # Hero
                'hero_badge_text', 'hero_title', 'hero_title_accent',
                'hero_subtitle', 'hero_image',
                'hero_cta_primary_text', 'hero_cta_secondary_text',
                # Embassy CTA
                'embassy_cta_eyebrow', 'embassy_cta_title',
                'embassy_cta_description', 'embassy_cta_note',
                # Official embassy
                'embassy_official_name', 'embassy_official_url',
                # Embassy disclaimer
                'embassy_disclaimer_enabled', 'embassy_disclaimer_text',
                # About
                'about_text', 'mission', 'vision',
                # Footer
                'footer_about', 'footer_copyright',
                # Contact
                'email', 'phone', 'address', 'office_hours',
                # Newsletter
                'newsletter_title', 'newsletter_description',
                # Social
                'facebook_url', 'twitter_url', 'instagram_url',
                'youtube_url', 'linkedin_url',
                # Discover Kenya page
                'discover_hero_title', 'discover_hero_subtitle', 'discover_hero_image',
                'discover_intro_title', 'discover_intro_text', 'discover_intro_image',
                'discover_culture_title', 'discover_culture_text',
                'discover_cuisine_title', 'discover_cuisine_text',
            ]
            widgets = {
                'tagline': djforms.TextInput(attrs={'class': 'form-control'}),
                'hero_subtitle': djforms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
                'embassy_cta_description': djforms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
                'embassy_cta_note': djforms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
                'embassy_disclaimer_text': djforms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
                'footer_about': djforms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
                'about_text': djforms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
                'mission': djforms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
                'vision': djforms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
                'address': djforms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
                'newsletter_description': djforms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
                'discover_hero_subtitle': djforms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
                'discover_intro_text': djforms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
                'discover_culture_text': djforms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
                'discover_cuisine_text': djforms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            }

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site settings updated successfully.')
            return redirect('portal:site_settings')
    else:
        form = SiteSettingsForm(instance=obj)

    return render(request, 'portal/site_settings.html', {'form': form, 'obj': obj})


def _form_class_for(Model, fields):
    """Build a ModelForm with crispy layout for the given model + fields.

    JSON fields become plain textareas with one-item-per-line convention.
    """
    from django import forms as djforms
    from django.forms import widgets as w
    from crispy_forms.helper import FormHelper
    from crispy_forms.layout import Submit
    import json

    overrides = {}
    json_field_names = []
    for f in fields:
        try:
            field_obj = Model._meta.get_field(f)
        except Exception:
            continue
        internal = field_obj.get_internal_type()
        if internal == 'TextField':
            overrides[f] = w.Textarea(attrs={'rows': 4, 'class': 'form-control'})
        elif internal == 'JSONField':
            json_field_names.append(f)
            # Widget set below after we swap field type
        elif internal == 'DateTimeField':
            overrides[f] = w.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        elif internal == 'DateField':
            overrides[f] = w.DateInput(attrs={'type': 'date', 'class': 'form-control'})

    Meta = type('Meta', (), {'model': Model, 'fields': fields, 'widgets': overrides})

    def __init__(self, *args, **kwargs):
        djforms.ModelForm.__init__(self, *args, **kwargs)
        # Replace each JSONField with a plain CharField(textarea)
        for f in json_field_names:
            if f in self.fields:
                self.fields[f] = djforms.CharField(
                    required=False,
                    widget=djforms.Textarea(attrs={
                        'rows': 5, 'class': 'form-control',
                        'placeholder': 'One item per line, e.g.:\nValid passport\nPassport photos\nBank statement'
                    }),
                    help_text='Enter one item per line.',
                )
                if self.instance and self.instance.pk:
                    val = getattr(self.instance, f, None)
                    if isinstance(val, list):
                        self.initial[f] = '\n'.join(str(v) for v in val)
                    elif isinstance(val, dict):
                        self.initial[f] = json.dumps(val, indent=2)
                    else:
                        self.initial[f] = ''
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.add_input(Submit('submit', 'Save', css_class='btn-primary btn-lg'))

    def clean(self):
        cleaned = djforms.ModelForm.clean(self) or {}
        # Convert text → list for JSON fields
        for f in json_field_names:
            raw = cleaned.get(f, '') or self.data.get(f, '')
            if isinstance(raw, str):
                raw_stripped = raw.strip()
                if not raw_stripped:
                    cleaned[f] = []
                else:
                    try:
                        parsed = json.loads(raw_stripped)
                        if isinstance(parsed, (list, dict)):
                            cleaned[f] = parsed
                        else:
                            raise ValueError
                    except (json.JSONDecodeError, ValueError):
                        lines = [line.strip() for line in raw_stripped.splitlines() if line.strip()]
                        cleaned[f] = lines
        return cleaned

    def save(self, commit=True):
        instance = djforms.ModelForm.save(self, commit=False)
        # Assign converted JSON field values from cleaned_data
        for f in json_field_names:
            if f in self.cleaned_data:
                setattr(instance, f, self.cleaned_data[f])
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    return type(f'{Model.__name__}AutoForm', (djforms.ModelForm,), {
        'Meta': Meta, '__init__': __init__, 'clean': clean, 'save': save,
    })
