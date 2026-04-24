from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, EventRegistration


# ---------- helpers ----------

def _user_is_member(user):
    """Active KCK membership check (uses memberships app context processor logic)."""
    try:
        from memberships.utils import user_active_membership
        return user_active_membership(user) is not None
    except Exception:
        return False


def _send_promotion_email(registration):
    """Notify a user that their waitlist seat was promoted to confirmed."""
    try:
        from core.models import SiteSettings
        site = SiteSettings.load()
        from_email = site.email or 'noreply@kenyakorea.com'
        u = registration.user
        e = registration.event
        if not u.email:
            return
        send_mail(
            subject=f'[KCK] You\'re in! A seat opened up for {e.title}',
            message=(
                f'Hi {u.get_full_name() or u.username},\n\n'
                f'A seat just opened up for "{e.title}" and you\'ve been promoted from the waitlist.\n\n'
                f'Event:    {e.title}\n'
                f'When:     {e.date.strftime("%A %d %B %Y, %H:%M")}\n'
                f'Location: {e.location}\n\n'
                f'Your seat is confirmed. If you can no longer attend, please cancel from the event page so we can give the spot to the next person on the waitlist.\n\n'
                f'See you there!\n\n'
                f'SOTE PAMOJA — All Together\n'
                f'Kenya Community in Korea'
            ),
            from_email=from_email,
            recipient_list=[u.email],
            fail_silently=True,
        )
        registration.promotion_email_sent_at = timezone.now()
        registration.save(update_fields=['promotion_email_sent_at'])
    except Exception:
        pass


def _next_in_line(event):
    """Return the next waitlisted registration to promote.

    Priority: KCK members first, then by waitlist_position (FIFO).
    """
    qs = (event.registrations.filter(status='waitlisted')
          .order_by('-is_member', 'waitlist_position', 'registered_at'))
    return qs.first()


def _promote_next(event):
    """Promote the next-in-line waitlisted registration. Returns the promoted obj or None."""
    nxt = _next_in_line(event)
    if not nxt:
        return None
    nxt.status = 'registered'
    nxt.promoted_at = timezone.now()
    nxt.waitlist_position = None
    nxt.save(update_fields=['status', 'promoted_at', 'waitlist_position'])
    _renumber_waitlist(event)
    _send_promotion_email(nxt)
    return nxt


def _renumber_waitlist(event):
    """Reassign waitlist_position 1..N preserving member-priority + FIFO order."""
    waiting = list(event.registrations.filter(status='waitlisted')
                   .order_by('-is_member', 'waitlist_position', 'registered_at'))
    for i, r in enumerate(waiting, start=1):
        if r.waitlist_position != i:
            r.waitlist_position = i
            r.save(update_fields=['waitlist_position'])


# ---------- public list / detail ----------

def event_list(request):
    events = Event.objects.filter(active=True, date__gte=timezone.now()).order_by('date')
    past_events = Event.objects.filter(active=True, date__lt=timezone.now()).order_by('-date')[:6]
    paginator = Paginator(events, 9)
    page = request.GET.get('page', 1)
    events_page = paginator.get_page(page)
    return render(request, 'events/event_list.html', {'events': events_page, 'past_events': past_events})


def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, active=True)
    my_reg = None
    if request.user.is_authenticated:
        my_reg = (EventRegistration.objects
                  .filter(user=request.user, event=event)
                  .exclude(status='cancelled')
                  .first())
    return render(request, 'events/event_detail.html', {
        'event': event,
        'my_reg': my_reg,
        # legacy
        'is_registered': bool(my_reg and my_reg.status == 'registered'),
    })


# ---------- register ----------

@login_required
def event_register(request, slug):
    event = get_object_or_404(Event, slug=slug, active=True)

    # Block past events
    if event.is_past:
        messages.error(request, 'This event has already taken place.')
        return redirect('events:event_detail', slug=slug)

    # Block past deadline
    if event.registration_deadline and timezone.now() > event.registration_deadline:
        messages.error(request, 'Registration deadline has passed.')
        return redirect('events:event_detail', slug=slug)

    is_member = _user_is_member(request.user)

    # Members-only events
    if event.members_only and not is_member:
        messages.error(request,
            'This event is for KCK members only. '
            'Become a member to attend, or check our other events.')
        return redirect('events:event_detail', slug=slug)

    # Atomic block — lock the event row so two concurrent registrations
    # cannot both pass the capacity check.
    with transaction.atomic():
        ev = Event.objects.select_for_update().get(pk=event.pk)

        # Already have an active registration?
        existing = (EventRegistration.objects
                    .filter(user=request.user, event=ev)
                    .exclude(status='cancelled')
                    .first())
        if existing:
            if existing.status == 'registered':
                messages.info(request, 'You are already registered for this event.')
            elif existing.status == 'waitlisted':
                messages.info(request,
                    f'You are already on the waitlist (#{existing.waitlist_position}).')
            return redirect('events:event_detail', slug=slug)

        # Re-using a previously-cancelled row?
        cancelled = EventRegistration.objects.filter(user=request.user, event=ev,
                                                     status='cancelled').first()

        confirmed_count = ev.registrations.filter(status='registered').count()
        full = ev.capacity and confirmed_count >= ev.capacity

        if not full:
            # Direct confirm
            if cancelled:
                cancelled.status = 'registered'
                cancelled.cancelled_at = None
                cancelled.is_member = is_member
                cancelled.waitlist_position = None
                cancelled.save()
            else:
                EventRegistration.objects.create(
                    user=request.user, event=ev,
                    status='registered', is_member=is_member,
                )
            messages.success(request, f'You\'re registered for "{ev.title}". See you there!')
            return redirect('events:event_detail', slug=slug)

        # Event is full
        if not ev.waitlist_enabled:
            messages.error(request, 'This event has reached capacity and the waitlist is closed.')
            return redirect('events:event_detail', slug=slug)

        # Add to waitlist
        if cancelled:
            cancelled.status = 'waitlisted'
            cancelled.cancelled_at = None
            cancelled.is_member = is_member
            cancelled.save()
            new_reg = cancelled
        else:
            new_reg = EventRegistration.objects.create(
                user=request.user, event=ev,
                status='waitlisted', is_member=is_member,
            )
        _renumber_waitlist(ev)
        new_reg.refresh_from_db()
        if is_member:
            messages.warning(request,
                f'The event is full, but as a KCK member you\'ve been placed at position #{new_reg.waitlist_position} on the waitlist. '
                f'You\'ll be emailed if a seat opens up.')
        else:
            messages.warning(request,
                f'The event is full. You\'ve been placed at position #{new_reg.waitlist_position} on the waitlist. '
                f'KCK members get priority — consider becoming a member.')
        return redirect('events:event_detail', slug=slug)


@login_required
def event_cancel_registration(request, slug):
    event = get_object_or_404(Event, slug=slug)
    with transaction.atomic():
        ev = Event.objects.select_for_update().get(pk=event.pk)
        reg = (EventRegistration.objects
               .filter(user=request.user, event=ev)
               .exclude(status='cancelled').first())
        if not reg:
            messages.info(request, 'You don\'t have an active registration for this event.')
            return redirect('events:event_detail', slug=slug)

        was_confirmed = (reg.status == 'registered')
        reg.status = 'cancelled'
        reg.cancelled_at = timezone.now()
        reg.waitlist_position = None
        reg.save(update_fields=['status', 'cancelled_at', 'waitlist_position'])

        # If we freed a confirmed seat, promote the next waitlisted person
        promoted = None
        if was_confirmed:
            promoted = _promote_next(ev)
        else:
            _renumber_waitlist(ev)

        if promoted:
            messages.success(request,
                f'Your registration was cancelled — and {promoted.user.get_full_name() or promoted.user.username} on the waitlist has been promoted into your spot.')
        else:
            messages.success(request, 'Your registration has been cancelled.')

    return redirect('events:event_detail', slug=slug)


def event_calendar(request):
    events = Event.objects.filter(active=True, date__gte=timezone.now()).order_by('date')
    return render(request, 'events/calendar.html', {'events': events})


def event_highlights(request):
    featured_events = Event.objects.filter(active=True, featured=True)[:12]
    past_with_images = Event.objects.filter(active=True, gallery_images__isnull=False).distinct()[:12]
    return render(request, 'events/highlights.html', {'featured_events': featured_events, 'past_events': past_with_images})
