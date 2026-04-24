"""Services app: apply URLs redirect to info (since KCK is not the embassy)."""
from django.test import TestCase


class LegacyApplyRedirectTest(TestCase):
    def test_visa_apply_redirects_to_types(self):
        r = self.client.get('/services/visa/apply/', follow=False)
        self.assertIn(r.status_code, (301, 302))
        self.assertEqual(r['Location'], '/services/visa/types/')

    def test_passport_apply_redirects_to_request(self):
        r = self.client.get('/services/passport/apply/', follow=False)
        self.assertIn(r.status_code, (301, 302))
        self.assertEqual(r['Location'], '/services/passport/request/')

    def test_no_apply_button_on_member_dashboard(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.create_user('dashuser', 'd@e.com', 'pw!123456')
        self.client.login(username='dashuser', password='pw!123456')
        r = self.client.get('/accounts/dashboard/')
        self.assertEqual(r.status_code, 200)
        # Ensure legacy "apply" CTAs are gone
        self.assertNotContains(r, 'visa_apply')
        self.assertNotContains(r, 'passport_apply')
        # Replacement CTAs present
        self.assertContains(r, 'Visa Info')
