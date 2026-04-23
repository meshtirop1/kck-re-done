from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import (
    Sport, Team, Player, Competition, Fixture, Lineup,
    SportsEvent, SportsNews,
)


def home(request):
    now = timezone.now()
    ctx = {
        'sports': Sport.objects.filter(active=True)[:8],
        'upcoming_fixtures': Fixture.objects.filter(
            status='scheduled', kickoff__gte=now
        ).select_related('home_team', 'away_team', 'competition').order_by('kickoff')[:5],
        'recent_results': Fixture.objects.filter(
            status='completed'
        ).select_related('home_team', 'away_team').order_by('-kickoff')[:5],
        'live_fixtures': Fixture.objects.filter(status='live').select_related('home_team', 'away_team'),
        'featured_teams': Team.objects.filter(active=True)[:6],
        'upcoming_events': SportsEvent.objects.filter(
            active=True, starts_at__gte=now
        ).order_by('starts_at')[:3],
        'featured_news': SportsNews.objects.filter(published=True, featured=True).first(),
        'latest_news': SportsNews.objects.filter(published=True)[:3],
        'active_competitions': Competition.objects.filter(active=True)[:4],
    }
    return render(request, 'sports/home.html', ctx)


def fixture_list(request, status=None):
    qs = Fixture.objects.all().select_related('home_team', 'away_team', 'competition')
    status = status or request.GET.get('status', 'upcoming')
    sport_slug = request.GET.get('sport')

    if status == 'upcoming':
        qs = qs.filter(status__in=['scheduled', 'live'], kickoff__gte=timezone.now()).order_by('kickoff')
    elif status == 'results':
        qs = qs.filter(status='completed').order_by('-kickoff')
    elif status == 'live':
        qs = qs.filter(status='live')
    else:
        qs = qs.order_by('-kickoff')

    if sport_slug:
        qs = qs.filter(home_team__sport__slug=sport_slug)

    sports = Sport.objects.filter(active=True)
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'sports/fixture_list.html', {
        'fixtures': page, 'status_filter': status, 'sport_slug': sport_slug, 'sports': sports,
    })


def fixture_detail(request, pk):
    fixture = get_object_or_404(
        Fixture.objects.select_related('home_team', 'away_team', 'competition', 'mvp'),
        pk=pk,
    )
    home_lineup = fixture.lineups.filter(team=fixture.home_team).select_related('player')
    away_lineup = fixture.lineups.filter(team=fixture.away_team).select_related('player')
    return render(request, 'sports/fixture_detail.html', {
        'fixture': fixture, 'home_lineup': home_lineup, 'away_lineup': away_lineup,
    })


def team_list(request):
    sport_slug = request.GET.get('sport')
    qs = Team.objects.filter(active=True).select_related('sport').annotate(
        player_count=Count('players', filter=Q(players__is_active=True))
    )
    if sport_slug:
        qs = qs.filter(sport__slug=sport_slug)
    return render(request, 'sports/team_list.html', {
        'teams': qs, 'sports': Sport.objects.filter(active=True), 'sport_slug': sport_slug,
    })


def team_detail(request, slug):
    team = get_object_or_404(Team, slug=slug, active=True)
    players = team.players.filter(is_active=True).order_by('jersey_number', 'full_name')
    upcoming_fixtures = Fixture.objects.filter(
        (Q(home_team=team) | Q(away_team=team)),
        status='scheduled', kickoff__gte=timezone.now(),
    ).order_by('kickoff')[:5]
    recent_fixtures = Fixture.objects.filter(
        (Q(home_team=team) | Q(away_team=team)),
        status='completed',
    ).order_by('-kickoff')[:5]
    return render(request, 'sports/team_detail.html', {
        'team': team, 'players': players,
        'upcoming_fixtures': upcoming_fixtures, 'recent_fixtures': recent_fixtures,
    })


def competition_list(request):
    return render(request, 'sports/competition_list.html', {
        'competitions': Competition.objects.filter(active=True).select_related('sport'),
    })


def competition_detail(request, slug):
    competition = get_object_or_404(Competition, slug=slug, active=True)
    fixtures = Fixture.objects.filter(competition=competition).select_related('home_team', 'away_team')

    standings = []
    for team in competition.teams.all():
        team_fixtures = fixtures.filter(Q(home_team=team) | Q(away_team=team), status='completed')
        w = d = l = gf = ga = 0
        for f in team_fixtures:
            if f.home_team_id == team.pk:
                gs, gc = f.home_score or 0, f.away_score or 0
            else:
                gs, gc = f.away_score or 0, f.home_score or 0
            gf += gs; ga += gc
            if gs > gc: w += 1
            elif gs < gc: l += 1
            else: d += 1
        standings.append({
            'team': team, 'played': w + d + l, 'wins': w, 'draws': d, 'losses': l,
            'gf': gf, 'ga': ga, 'gd': gf - ga, 'points': w * 3 + d,
        })
    standings.sort(key=lambda x: (-x['points'], -x['gd'], -x['gf']))

    return render(request, 'sports/competition_detail.html', {
        'competition': competition, 'fixtures': fixtures.order_by('kickoff'),
        'standings': standings,
    })


def sport_list(request):
    return render(request, 'sports/sport_list.html', {
        'sports': Sport.objects.filter(active=True).annotate(team_count=Count('teams'))
    })


def sport_detail(request, slug):
    sport = get_object_or_404(Sport, slug=slug, active=True)
    teams = sport.teams.filter(active=True)
    upcoming = Fixture.objects.filter(
        home_team__sport=sport, status='scheduled', kickoff__gte=timezone.now()
    ).order_by('kickoff')[:5]
    results = Fixture.objects.filter(
        home_team__sport=sport, status='completed'
    ).order_by('-kickoff')[:5]
    return render(request, 'sports/sport_detail.html', {
        'sport': sport, 'teams': teams,
        'upcoming': upcoming, 'results': results,
    })


def event_list(request):
    qs = SportsEvent.objects.filter(active=True)
    when = request.GET.get('when', 'upcoming')
    if when == 'upcoming':
        qs = qs.filter(starts_at__gte=timezone.now()).order_by('starts_at')
    elif when == 'past':
        qs = qs.filter(starts_at__lt=timezone.now()).order_by('-starts_at')
    return render(request, 'sports/event_list.html', {
        'events': qs, 'when': when,
    })


def event_detail(request, slug):
    event = get_object_or_404(SportsEvent, slug=slug, active=True)
    return render(request, 'sports/event_detail.html', {'event': event})


def news_list(request):
    qs = SportsNews.objects.filter(published=True)
    paginator = Paginator(qs, 9)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'sports/news_list.html', {'news': page})


def news_detail(request, slug):
    article = get_object_or_404(SportsNews, slug=slug, published=True)
    related = SportsNews.objects.filter(
        published=True
    ).exclude(pk=article.pk).order_by('-published_at')[:3]
    return render(request, 'sports/news_detail.html', {
        'article': article, 'related': related,
    })
