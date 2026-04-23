from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Event, EventRegistration

def event_list(request):
    events = Event.objects.filter(active=True, date__gte=timezone.now()).order_by('date')
    past_events = Event.objects.filter(active=True, date__lt=timezone.now()).order_by('-date')[:6]
    paginator = Paginator(events, 9)
    page = request.GET.get('page', 1)
    events_page = paginator.get_page(page)
    return render(request, 'events/event_list.html', {'events': events_page, 'past_events': past_events})

def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, active=True)
    is_registered = False
    if request.user.is_authenticated:
        is_registered = EventRegistration.objects.filter(user=request.user, event=event).exists()
    return render(request, 'events/event_detail.html', {'event': event, 'is_registered': is_registered})

@login_required
def event_register(request, slug):
    event = get_object_or_404(Event, slug=slug, active=True)

    if EventRegistration.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('events:event_detail', slug=slug)

    if event.capacity and event.registration_count >= event.capacity:
        messages.error(request, 'This event has reached its capacity.')
        return redirect('events:event_detail', slug=slug)

    if event.registration_deadline and timezone.now() > event.registration_deadline:
        messages.error(request, 'Registration deadline has passed.')
        return redirect('events:event_detail', slug=slug)

    EventRegistration.objects.create(user=request.user, event=event)
    messages.success(request, f'You have been registered for {event.title}.')
    return redirect('events:event_detail', slug=slug)

@login_required
def event_cancel_registration(request, slug):
    event = get_object_or_404(Event, slug=slug)
    EventRegistration.objects.filter(user=request.user, event=event).delete()
    messages.success(request, 'Your registration has been cancelled.')
    return redirect('events:event_detail', slug=slug)

def event_calendar(request):
    events = Event.objects.filter(active=True, date__gte=timezone.now()).order_by('date')
    return render(request, 'events/calendar.html', {'events': events})

def event_highlights(request):
    featured_events = Event.objects.filter(active=True, featured=True)[:12]
    past_with_images = Event.objects.filter(active=True, gallery_images__isnull=False).distinct()[:12]
    return render(request, 'events/highlights.html', {'featured_events': featured_events, 'past_events': past_with_images})
