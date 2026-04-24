"""Membership lifecycle: apply → declare payment → verify → activate → renew."""
from datetime import date, timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from PIL import Image

from leaders.models import Leader, LeaderPermission
from memberships.models import Membership, MembershipTier

User = get_user_model()


def _make_png_upload(name='proof.jpg'):
    """Return a SimpleUploadedFile-like object for a 10×10 JPEG."""
    from django.core.files.uploadedfile import SimpleUploadedFile
    buf = BytesIO()
    Image.new('RGB', (10, 10), color='red').save(buf, 'JPEG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/jpeg')


class MembershipLifecycleTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tier = MembershipTier.objects.create(
            name='Test Individual', annual_amount=50000, currency='KRW', active=True,
        )
        cls.user = User.objects.create_user('memberu', 'm@example.com', 'pw!123456')
        # Treasurer
        cls.treasurer = User.objects.create_user('trea', 't@example.com', 'pw!123456')
        leader = Leader.objects.create(user=cls.treasurer, role='treasurer')
        # Ensure perms are fresh (signal creates defaults, but explicit is safer)
        leader.permissions.can_manage_memberships = True
        leader.permissions.save()

    def test_apply_creates_pending_membership(self):
        self.client.login(username='memberu', password='pw!123456')
        r = self.client.get('/membership/apply/', follow=False)
        self.assertIn(r.status_code, (301, 302))
        m = Membership.objects.get(user=self.user)
        self.assertEqual(m.status, 'pending_payment')
        self.assertTrue(m.reference_code.startswith('KCK-M-'))
        self.assertIsNone(m.member_number)

    def test_full_flow_to_activation(self):
        self.client.login(username='memberu', password='pw!123456')
        # 1. Apply
        self.client.get('/membership/apply/')
        m = Membership.objects.get(user=self.user)
        # 2. Declare payment
        r = self.client.post(f'/membership/my/{m.pk}/declare-payment/', {
            'claimed_amount': str(m.expected_amount),
            'claimed_date': str(date.today()),
            'notes': 'Test transfer',
            'proof_image': _make_png_upload(),
        })
        self.assertIn(r.status_code, (301, 302))
        m.refresh_from_db()
        self.assertEqual(m.status, 'awaiting_verification')
        # 3. Treasurer verifies
        self.client.logout()
        self.client.login(username='trea', password='pw!123456')
        r = self.client.post(f'/membership/treasurer/{m.pk}/',
            {'action': 'verify', 'notes': 'Confirmed on bank statement'})
        self.assertIn(r.status_code, (301, 302))
        m.refresh_from_db()
        self.assertEqual(m.status, 'active')
        self.assertIsNotNone(m.member_number)
        self.assertTrue(m.member_number.startswith('KCK-'))
        self.assertIsNotNone(m.period_start)
        self.assertIsNotNone(m.period_end)
        # 4. PDF card generates for active member
        self.client.logout()
        self.client.login(username='memberu', password='pw!123456')
        r = self.client.get(f'/membership/my/{m.pk}/card.pdf')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        # 5. Public verify page shows valid
        self.client.logout()
        r = self.client.get(f'/membership/verify/{m.member_number}/')
        self.assertContains(r, 'Valid Member')

    def test_renewal_reuses_member_number(self):
        """The UNIQUE constraint on member_number was a real bug. Renewals must reuse it."""
        # Year 1: create + activate
        self.client.login(username='memberu', password='pw!123456')
        self.client.get('/membership/apply/')
        m1 = Membership.objects.get(user=self.user)
        from memberships.utils import activate_membership
        activate_membership(m1, verifier=self.treasurer)
        m1.refresh_from_db()
        original_number = m1.member_number
        self.assertTrue(original_number)

        # Year 2: expire then re-apply
        m1.status = 'expired'
        m1.save()
        self.client.get('/membership/apply/')
        m2 = Membership.objects.filter(user=self.user).exclude(pk=m1.pk).first()
        self.assertIsNotNone(m2)
        activate_membership(m2, verifier=self.treasurer)
        m2.refresh_from_db()
        self.assertEqual(m2.member_number, original_number,
            'Renewal should reuse the original member number')

    def test_non_treasurer_cannot_access_treasurer_pages(self):
        """Regression test for the redirect-loop bug."""
        self.client.login(username='memberu', password='pw!123456')
        r = self.client.get('/membership/treasurer/')
        self.assertEqual(r.status_code, 403, 'Non-treasurer should get 403, not redirect loop')

    def test_anonymous_hits_login(self):
        r = self.client.get('/membership/treasurer/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])
