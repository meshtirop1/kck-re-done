"""Role permissions — visibility + enforcement at view level."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from leaders.models import Leader

User = get_user_model()


class PermissionEnforcementTest(TestCase):
    """Every gated URL must 403 for users without the permission, 200 with."""

    @classmethod
    def setUpTestData(cls):
        # Superuser — should have all access
        cls.admin = User.objects.create_superuser('adm', 'a@example.com', 'pw!123456')
        # Regular member — no leader profile
        cls.member = User.objects.create_user('mem', 'm@example.com', 'pw!123456')
        # Leaders
        for role in ('president', 'treasurer', 'secretary', 'welfare', 'committee'):
            u = User.objects.create_user(role, f'{role}@example.com', 'pw!123456')
            Leader.objects.create(user=u, role=role)
            setattr(cls, f'u_{role}', u)

    def _get(self, username, url):
        c = self.client_class()
        c.login(username=username, password='pw!123456')
        return c.get(url, follow=False)

    def test_roles_overview_only_president(self):
        self.assertEqual(self._get('president', '/leaders/manage/roles/').status_code, 200)
        self.assertEqual(self._get('treasurer', '/leaders/manage/roles/').status_code, 403)
        self.assertEqual(self._get('mem', '/leaders/manage/roles/').status_code, 403)
        self.assertEqual(self._get('adm', '/leaders/manage/roles/').status_code, 200)

    def test_treasurer_dashboard(self):
        self.assertEqual(self._get('treasurer', '/membership/treasurer/').status_code, 200)
        self.assertEqual(self._get('mem', '/membership/treasurer/').status_code, 403)
        self.assertEqual(self._get('welfare', '/membership/treasurer/').status_code, 403)
        self.assertEqual(self._get('adm', '/membership/treasurer/').status_code, 200)

    def test_oversight_dashboard(self):
        self.assertEqual(self._get('president', '/membership/oversight/').status_code, 200)
        self.assertEqual(self._get('secretary', '/membership/oversight/').status_code, 200)
        self.assertEqual(self._get('mem', '/membership/oversight/').status_code, 403)

    def test_portal_access(self):
        self.assertEqual(self._get('president', '/portal/').status_code, 200)
        self.assertEqual(self._get('treasurer', '/portal/').status_code, 200)
        self.assertEqual(self._get('mem', '/portal/').status_code, 403,
            'regular members should be 403, not redirect-looped')

    def test_portal_crud_gated_by_content_perm(self):
        # Treasurer has no can_manage_content → blocked from visa-types CRUD
        self.assertEqual(self._get('treasurer', '/portal/visa-types/').status_code, 403)
        # President has every perm → allowed
        self.assertEqual(self._get('president', '/portal/visa-types/').status_code, 200)

    def test_anonymous_login_redirect(self):
        c = self.client_class()
        r = c.get('/portal/', follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])


class SidebarVisibilityTest(TestCase):
    """Sidebar link visibility depends on the user's permissions."""

    @classmethod
    def setUpTestData(cls):
        cls.president = User.objects.create_user('sprez', 'p@e.com', 'pw!123456')
        Leader.objects.create(user=cls.president, role='president')
        cls.treasurer = User.objects.create_user('stre', 't@e.com', 'pw!123456')
        Leader.objects.create(user=cls.treasurer, role='treasurer')

    def test_president_sees_roles_and_permissions_link(self):
        self.client.login(username='sprez', password='pw!123456')
        r = self.client.get('/portal/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Roles &amp; Permissions')

    def test_treasurer_does_not_see_roles_and_permissions_link(self):
        self.client.login(username='stre', password='pw!123456')
        r = self.client.get('/portal/')
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Roles &amp; Permissions')

    def test_treasurer_sees_membership_treasurer_link(self):
        self.client.login(username='stre', password='pw!123456')
        r = self.client.get('/portal/')
        self.assertContains(r, 'Memberships (Treasurer)')

    def test_treasurer_does_not_see_content_links(self):
        self.client.login(username='stre', password='pw!123456')
        r = self.client.get('/portal/')
        # Visa Types CRUD link must NOT appear — they can't edit content
        self.assertNotContains(r, 'href="/portal/visa-types/"')
