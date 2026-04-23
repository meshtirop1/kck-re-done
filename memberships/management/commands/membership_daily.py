"""Daily membership housekeeping:
  - expire memberships past period_end
  - send 30-day, 7-day reminders
  - send post-expiry notice
Run this once a day via cron / Windows Task Scheduler:

    python manage.py membership_daily
"""
from datetime import timedelta
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from core.models import SiteSettings
from memberships.models import Membership
from memberships.utils import log_action


class Command(BaseCommand):
    help = 'Daily membership housekeeping: expire, remind, notify'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
            help="Don't send emails or update DB; just report what would happen.")

    def handle(self, *args, **opts):
        dry = opts['dry_run']
        today = timezone.now().date()
        now = timezone.now()
        site = SiteSettings.load()
        from_email = site.email or 'noreply@kenyakorea.com'
        base_url = 'https://kenyakorea.com'  # adjust if needed

        n_expired = 0
        n_30 = 0
        n_7 = 0
        n_expiry_notified = 0

        # ---------- Expire ----------
        to_expire = Membership.objects.filter(
            status=Membership.STATUS_ACTIVE,
            period_end__lt=today,
        )
        for m in to_expire:
            self.stdout.write(f'Expiring {m.reference_code} (ended {m.period_end})')
            if not dry:
                m.status = Membership.STATUS_EXPIRED
                m.save(update_fields=['status'])
                log_action(membership=m, action='expire',
                    description=f'Membership expired (period ended {m.period_end})',
                    metadata={'period_end': str(m.period_end)})
            n_expired += 1

        # ---------- 30-day reminder ----------
        cutoff_30 = today + timedelta(days=30)
        to_remind_30 = Membership.objects.filter(
            status=Membership.STATUS_ACTIVE,
            period_end__lte=cutoff_30,
            period_end__gt=today + timedelta(days=7),
            reminder_30_sent_at__isnull=True,
        )
        for m in to_remind_30:
            self.stdout.write(f'30-day reminder for {m.reference_code}')
            if not dry and m.user.email:
                _send_reminder(m, days=30, from_email=from_email, site=site, base_url=base_url)
                m.reminder_30_sent_at = now
                m.save(update_fields=['reminder_30_sent_at'])
                log_action(membership=m, action='reminder_sent',
                    description='30-day expiry reminder sent')
            n_30 += 1

        # ---------- 7-day reminder ----------
        cutoff_7 = today + timedelta(days=7)
        to_remind_7 = Membership.objects.filter(
            status=Membership.STATUS_ACTIVE,
            period_end__lte=cutoff_7,
            period_end__gte=today,
            reminder_7_sent_at__isnull=True,
        )
        for m in to_remind_7:
            self.stdout.write(f'7-day reminder for {m.reference_code}')
            if not dry and m.user.email:
                _send_reminder(m, days=7, from_email=from_email, site=site, base_url=base_url)
                m.reminder_7_sent_at = now
                m.save(update_fields=['reminder_7_sent_at'])
                log_action(membership=m, action='reminder_sent',
                    description='7-day expiry reminder sent')
            n_7 += 1

        # ---------- Post-expiry notice ----------
        to_notify = Membership.objects.filter(
            status=Membership.STATUS_EXPIRED,
            expiry_notified_at__isnull=True,
        )
        for m in to_notify:
            self.stdout.write(f'Expiry notice for {m.reference_code}')
            if not dry and m.user.email:
                _send_expiry_notice(m, from_email=from_email, site=site, base_url=base_url)
                m.expiry_notified_at = now
                m.save(update_fields=['expiry_notified_at'])
                log_action(membership=m, action='reminder_sent',
                    description='Post-expiry notice sent')
            n_expiry_notified += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Expired: {n_expired} · 30-day: {n_30} · 7-day: {n_7} · Expired-notified: {n_expiry_notified}'
            f'{" (dry run)" if dry else ""}'))


def _send_reminder(membership, days, from_email, site, base_url):
    subject = f'[KCK] Your membership expires in {days} day{"s" if days != 1 else ""}'
    body = (
        f'Hi {membership.user.get_full_name() or membership.user.username},\n\n'
        f'Your KCK membership (number {membership.member_number}) expires on '
        f'{membership.period_end.strftime("%d %B %Y")}.\n\n'
        f'Renew now to keep your benefits active.\n\n'
        f'{base_url}/membership/\n\n'
        f'SOTE PAMOJA — All Together\n'
        f'Kenya Community in Korea'
    )
    send_mail(subject, body, from_email, [membership.user.email], fail_silently=True)


def _send_expiry_notice(membership, from_email, site, base_url):
    subject = '[KCK] Your membership has expired'
    body = (
        f'Hi {membership.user.get_full_name() or membership.user.username},\n\n'
        f'Your KCK membership (number {membership.member_number}) expired on '
        f'{membership.period_end.strftime("%d %B %Y")}.\n\n'
        f'Benefits are paused until you renew. Renew here:\n'
        f'{base_url}/membership/\n\n'
        f'SOTE PAMOJA — All Together\n'
        f'Kenya Community in Korea'
    )
    send_mail(subject, body, from_email, [membership.user.email], fail_silently=True)
