"""Subdomain-based URL routing.

sports.kenyakorea.com  → kck_project.sports_urls  (sports site)
kenyakorea.com         → kck_project.urls          (main site)

For local development, sports.localhost:8000 also works because most browsers
resolve any *.localhost to 127.0.0.1 by default.

A ?subdomain=sports query string / cookie also forces the sports URL conf
(useful when testing behind a reverse proxy without real subdomain DNS).
"""
from django.conf import settings


SPORTS_HOSTS = {
    'sports.kenyakorea.com',
    'sports.localhost',
    'sports.127.0.0.1',
}

MAIN_HOSTS = {
    'kenyakorea.com',
    'www.kenyakorea.com',
    'localhost',
    '127.0.0.1',
}


class SubdomainURLRoutingMiddleware:
    """Switch request.urlconf based on the hostname (and allow override for dev)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()

        # Query-string override (for dev: http://127.0.0.1:8000/?subdomain=sports)
        override = request.GET.get('subdomain')
        if override == 'sports':
            request.session['_subdomain'] = 'sports'
        elif override == 'main':
            request.session.pop('_subdomain', None)

        session_override = request.session.get('_subdomain') if hasattr(request, 'session') else None

        is_sports = (
            host in SPORTS_HOSTS
            or host.startswith('sports.')
            or session_override == 'sports'
        )

        if is_sports:
            request.urlconf = 'kck_project.sports_urls'
            request.is_sports_site = True
        else:
            request.is_sports_site = False

        return self.get_response(request)
