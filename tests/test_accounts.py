"""Auth flow: register, login, logout, password reset."""
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationTest(TestCase):
    def test_register_form_renders(self):
        r = self.client.get('/accounts/register/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Register')

    def test_register_creates_user_and_logs_in(self):
        r = self.client.post('/accounts/register/', {
            'username': 'testjohn',
            'email': 'testjohn@example.com',
            'first_name': 'Test',
            'last_name': 'John',
            'password1': 'strongPass!123',
            'password2': 'strongPass!123',
        }, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(User.objects.filter(username='testjohn').exists())
        # After registration the user should be logged in
        self.assertTrue(self.client.session.get('_auth_user_id'))


class LoginLogoutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', email='login@example.com', password='pw!2345'
        )

    def test_login_success(self):
        r = self.client.post('/accounts/login/',
            {'username': 'loginuser', 'password': 'pw!2345'}, follow=False)
        self.assertIn(r.status_code, (301, 302))
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_login_wrong_password(self):
        r = self.client.post('/accounts/login/',
            {'username': 'loginuser', 'password': 'nope'}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_logout(self):
        self.client.login(username='loginuser', password='pw!2345')
        r = self.client.post('/accounts/logout/', follow=False)
        self.assertIn(r.status_code, (301, 302))
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_dashboard_requires_login(self):
        r = self.client.get('/accounts/dashboard/', follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])


class PasswordResetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='pwreset', email='pwreset@example.com', password='old!pw1234'
        )

    def test_reset_form_renders(self):
        r = self.client.get('/accounts/password-reset/')
        self.assertEqual(r.status_code, 200)

    def test_reset_email_flow(self):
        r = self.client.post('/accounts/password-reset/',
            {'email': 'pwreset@example.com'}, follow=False)
        self.assertIn(r.status_code, (301, 302))
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['pwreset@example.com'])
        self.assertIn('Reset your password', msg.subject)
        # The multipart HTML version should exist and be branded
        self.assertTrue(msg.alternatives)
        html_body, mime = msg.alternatives[0]
        self.assertEqual(mime, 'text/html')
        self.assertIn('Reset my password', html_body)
        self.assertIn('SOTE PAMOJA', html_body)
        self.assertIn('/accounts/reset/', msg.body)
