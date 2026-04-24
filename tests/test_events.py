"""Event registration, waitlist, member priority, deadline handling."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from events_app.models import Event, EventRegistration
from memberships.models import Membership, MembershipTier

User = get_user_model()


class WaitlistTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            title='Capacity Test',
            slug='capacity-test',
            description='Testing waitlist',
            date=timezone.now() + timedelta(days=10),
            location='Seoul',
            capacity=2,
            waitlist_enabled=True,
        )
        for i in range(1, 5):
            u = User.objects.create_user(
                f'evuser{i}', f'e{i}@example.com', 'pw!123456'
            )
            setattr(cls, f'u{i}', u)
        # Make u3 an active paid member (priority)
        tier = MembershipTier.objects.create(
            name='Test Tier', annual_amount=50000, currency='KRW', active=True,
        )
        import datetime
        Membership.objects.create(
            user=cls.u3, tier=tier, expected_amount=50000,
            currency='KRW', status='active',
            period_start=datetime.date.today(),
            period_end=datetime.date.today() + datetime.timedelta(days=365),
            member_number='KCK-2026-TEST01',
        )

    def _register(self, user):
        c = self.client_class()
        c.login(username=user.username, password='pw!123456')
        return c.post(f'/events/{self.event.slug}/register/', follow=False)

    def _cancel(self, user):
        c = self.client_class()
        c.login(username=user.username, password='pw!123456')
        return c.post(f'/events/{self.event.slug}/cancel/', follow=False)

    def test_first_two_get_confirmed_third_is_waitlisted(self):
        self._register(self.u1)
        self._register(self.u2)
        self._register(self.u4)  # non-member, registers 3rd
        self.event.refresh_from_db()
        self.assertEqual(self.event.registration_count, 2)
        self.assertTrue(self.event.is_full)
        wl = EventRegistration.objects.filter(event=self.event, status='waitlisted')
        self.assertEqual(wl.count(), 1)
        self.assertEqual(wl.first().user, self.u4)

    def test_member_jumps_queue_over_non_member(self):
        self._register(self.u1)
        self._register(self.u2)        # capacity reached
        self._register(self.u4)         # non-member → waitlist #1 at this point
        self._register(self.u3)         # member     → jumps to #1
        waitlist = EventRegistration.objects.filter(event=self.event, status='waitlisted').order_by('waitlist_position')
        self.assertEqual(waitlist[0].user, self.u3, 'member should be first')
        self.assertEqual(waitlist[1].user, self.u4, 'non-member second')

    def test_cancel_promotes_next_waitlisted(self):
        self._register(self.u1)
        self._register(self.u2)
        self._register(self.u4)   # waitlist #1
        self._cancel(self.u1)
        self.event.refresh_from_db()
        self.assertEqual(self.event.registration_count, 2)
        u4_reg = EventRegistration.objects.get(event=self.event, user=self.u4)
        self.assertEqual(u4_reg.status, 'registered')
        self.assertIsNotNone(u4_reg.promoted_at)

    def test_promotion_email_sent(self):
        from django.core import mail
        self._register(self.u1)
        self._register(self.u2)
        self._register(self.u4)
        mail.outbox = []
        self._cancel(self.u1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('seat opened up', mail.outbox[0].subject.lower())
        self.assertEqual(mail.outbox[0].to, [self.u4.email])

    def test_cannot_double_register(self):
        self._register(self.u1)
        r = self._register(self.u1)
        self.assertIn(r.status_code, (301, 302))
        count = EventRegistration.objects.filter(
            event=self.event, user=self.u1
        ).exclude(status='cancelled').count()
        self.assertEqual(count, 1)


class DeadlineTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title='Deadline Test',
            slug='deadline-test',
            description='x',
            date=timezone.now() + timedelta(days=10),
            location='Seoul',
            capacity=5,
            registration_deadline=timezone.now() - timedelta(hours=1),  # past
        )
        self.user = User.objects.create_user('du1', 'du1@e.com', 'pw!123456')

    def test_registration_blocked_after_deadline(self):
        self.client.login(username='du1', password='pw!123456')
        r = self.client.post(f'/events/{self.event.slug}/register/', follow=False)
        self.assertIn(r.status_code, (301, 302))
        self.assertEqual(EventRegistration.objects.filter(event=self.event).count(), 0)

    def test_detail_page_shows_registration_closed(self):
        r = self.client.get(f'/events/{self.event.slug}/')
        self.assertContains(r, 'Registration closed')
        self.assertNotContains(r, 'Register Now')


class MembersOnlyTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title='Members Only',
            slug='members-only',
            description='x',
            date=timezone.now() + timedelta(days=10),
            location='Seoul',
            members_only=True,
            capacity=10,
        )

    def test_non_member_blocked(self):
        u = User.objects.create_user('nonm', 'n@e.com', 'pw!123456')
        self.client.login(username='nonm', password='pw!123456')
        r = self.client.post(f'/events/{self.event.slug}/register/', follow=False)
        self.assertIn(r.status_code, (301, 302))
        self.assertEqual(EventRegistration.objects.filter(event=self.event).count(), 0)
