"""Smoke tests for public (anonymous-accessible) pages."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class PublicPageSmokeTest(TestCase):
    """Every public URL must render 200 and NOT leak a 5xx/404."""

    @classmethod
    def setUpTestData(cls):
        # Seed a minimal President leader — the /presidents-message/ page
        # needs one to render its hero without an attribute error.
        from leaders.models import Leader
        u = User.objects.create_user('testpres', 'p@e.com', 'pw!123456',
                                     first_name='Test', last_name='President')
        Leader.objects.create(user=u, role='president', is_active=True,
                              message='Welcome.', message_title='A Message',
                              show_message_on_home=True)

    URLS = [
        '/',
        '/about/',
        '/contact/',
        '/ambassador/',
        '/embassy-history/',
        '/visit/',
        '/discover/',
        '/presidents-message/',
        '/privacy/',
        '/terms/',
        '/data-handling/',
        '/search/?q=visa',
        '/services/visa/types/',
        '/services/visa/services/',
        '/services/visa/issues/',
        '/services/visa/faqs/',
        '/services/passport/request/',
        '/services/faqs/',
        '/services/highlights/',
        '/events/',
        '/events/calendar/',
        '/events/highlights/',
        '/community/',
        '/community/news/',
        '/community/testimonials/',
        '/community/mission/',
        '/community/history/',
        '/community/location/',
        '/leaders/',
        '/embassy-services/',
        '/embassy-services/services/',
        '/certificates/',
        '/endorsements/',
        '/communications/',
        '/communications/announcements/',
        '/membership/',
        '/market/',
        '/accounts/login/',
        '/accounts/register/',
        '/accounts/password-reset/',
        '/sports/',
        '/sports/fixtures/',
        '/sports/results/',
        '/sports/teams/',
        '/sports/competitions/',
        '/sports/events/',
        '/sports/news/',
    ]

    def test_all_public_urls_render_ok(self):
        for url in self.URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f'{url} returned {response.status_code}')


class ErrorPageTest(TestCase):
    """Custom 404/403/500 templates render cleanly."""

    def test_404_returns_branded_page(self):
        # In DEBUG=True the test client gets Django's technical 404; under
        # DEBUG=False (TEST overrides it) the custom handler fires.
        with self.settings(DEBUG=False):
            response = self.client.get('/this-does-not-exist-xyz/')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Take me home', response.content)

    def test_custom_404_template_renders_standalone(self):
        from django.template.loader import render_to_string
        html = render_to_string('404.html')
        self.assertIn('Page Not Found', html)
        self.assertIn('Take me home', html)

    def test_custom_403_template_renders_standalone(self):
        from django.template.loader import render_to_string
        html = render_to_string('403.html')
        self.assertIn('Access denied', html)

    def test_custom_500_handler_wired(self):
        """Verify the 500 handler is correctly registered (calling it in tests
        requires triggering a real exception, so we just check the URL conf)."""
        from django.urls import get_resolver
        resolver = get_resolver()
        handler = resolver.urlconf_module.handler500
        self.assertEqual(handler, 'core.views.custom_500')
