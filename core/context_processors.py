"""Site-wide context — everything syncs from DB via SiteSettings singleton."""
from community.models import Announcement
from django.utils import timezone
from django.conf import settings
from core.models import SiteSettings


def site_context(request):
    """Make site-wide data available in all templates.

    DB values (SiteSettings) take priority over settings.py defaults,
    so admins can edit everything live from the portal.
    """
    now = timezone.now()
    active_announcements = Announcement.objects.filter(
        active=True, starts_at__lte=now, ends_at__gte=now
    )

    ss = SiteSettings.load()

    return {
        # Expose entire SiteSettings object
        'site_settings': ss,

        # Legacy shortcuts (used throughout templates) — all pulled from DB now
        'SITE_NAME': ss.site_name or settings.SITE_NAME,
        'SITE_SHORT_NAME': ss.site_short_name or settings.SITE_SHORT_NAME,
        'SITE_EMAIL': ss.email or settings.SITE_EMAIL,
        'SITE_PHONE': ss.phone or settings.SITE_PHONE,
        'SITE_ADDRESS': ss.address or getattr(settings, 'SITE_ADDRESS', 'Seoul, South Korea'),
        'SITE_TAGLINE': ss.tagline,

        # Slogan
        'SLOGAN': ss.slogan or 'SOTE PAMOJA',
        'SLOGAN_TRANSLATION': ss.slogan_translation or 'All Together',
        'SLOGAN_DESCRIPTION': ss.slogan_description or 'the spirit of our community',

        # Announcements banner
        'active_announcements': active_announcements,
    }
