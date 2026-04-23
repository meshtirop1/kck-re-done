"""KCK Sports — community sports, fixtures, results, teams.
Served from sports.kenyakorea.com via subdomain routing.
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone


SPORT_CATEGORY_CHOICES = [
    ('football', 'Football (Soccer)'),
    ('rugby', 'Rugby'),
    ('basketball', 'Basketball'),
    ('volleyball', 'Volleyball'),
    ('athletics', 'Athletics / Track & Field'),
    ('marathon', 'Marathon / Running'),
    ('tennis', 'Tennis'),
    ('table_tennis', 'Table Tennis'),
    ('netball', 'Netball'),
    ('cricket', 'Cricket'),
    ('chess', 'Chess'),
    ('other', 'Other'),
]


class Sport(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=120, blank=True)
    category = models.CharField(max_length=30, choices=SPORT_CATEGORY_CHOICES, default='football')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True, default='⚽')
    cover_image = models.ImageField(upload_to='sports/covers/', blank=True, null=True)
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='teams')
    short_name = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='sports/teams/', blank=True, null=True)
    color_primary = models.CharField(max_length=20, default='#00A651')
    color_secondary = models.CharField(max_length=20, default='#000000')
    founded = models.DateField(null=True, blank=True)
    captain = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='teams_captained')
    home_venue = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sport', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 2
            while Team.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def total_matches(self):
        return Fixture.objects.filter(
            models.Q(home_team=self) | models.Q(away_team=self),
            status='completed'
        ).count()

    @property
    def wins(self):
        return (Fixture.objects.filter(home_team=self, status='completed',
                                       home_score__gt=models.F('away_score')).count()
                + Fixture.objects.filter(away_team=self, status='completed',
                                         away_score__gt=models.F('home_score')).count())

    @property
    def losses(self):
        return (Fixture.objects.filter(home_team=self, status='completed',
                                       home_score__lt=models.F('away_score')).count()
                + Fixture.objects.filter(away_team=self, status='completed',
                                         away_score__lt=models.F('home_score')).count())

    @property
    def draws(self):
        return Fixture.objects.filter(
            models.Q(home_team=self) | models.Q(away_team=self),
            status='completed', home_score=models.F('away_score')).count()


POSITION_CHOICES = [
    ('gk', 'Goalkeeper'),
    ('df', 'Defender'),
    ('mf', 'Midfielder'),
    ('fw', 'Forward'),
    ('c', 'Center'),
    ('g', 'Guard'),
    ('f', 'Forward'),
    ('cap', 'Captain'),
    ('any', 'Any / Multi-position'),
]


class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='player_profiles')
    full_name = models.CharField(max_length=255)
    jersey_number = models.IntegerField(null=True, blank=True)
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, default='any')
    photo = models.ImageField(upload_to='sports/players/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    is_captain = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['team', 'jersey_number', 'full_name']

    def __str__(self):
        return f'{self.full_name} ({self.team.name})'


class Competition(models.Model):
    COMPETITION_TYPE_CHOICES = [
        ('league', 'League'),
        ('tournament', 'Tournament / Cup'),
        ('friendly', 'Friendly Series'),
        ('championship', 'Championship'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='competitions')
    competition_type = models.CharField(max_length=20, choices=COMPETITION_TYPE_CHOICES, default='tournament')
    season = models.CharField(max_length=50, default='2026')
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='sports/competitions/', blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    teams = models.ManyToManyField(Team, blank=True, related_name='competitions')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.name}-{self.season}')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.season})'


FIXTURE_STATUS_CHOICES = [
    ('scheduled', 'Scheduled'),
    ('live', 'Live'),
    ('completed', 'Completed'),
    ('postponed', 'Postponed'),
    ('cancelled', 'Cancelled'),
]


class Fixture(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='fixtures',
        null=True, blank=True)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_fixtures')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_fixtures')
    kickoff = models.DateTimeField()
    venue = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=FIXTURE_STATUS_CHOICES, default='scheduled')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    match_report = models.TextField(blank=True)
    highlights_video_url = models.URLField(blank=True)
    mvp = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mvp_fixtures')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-kickoff']

    def __str__(self):
        return f'{self.home_team.short_name or self.home_team.name} vs {self.away_team.short_name or self.away_team.name}'

    @property
    def is_past(self):
        return self.kickoff < timezone.now()

    @property
    def winner(self):
        if self.status != 'completed' or self.home_score is None or self.away_score is None:
            return None
        if self.home_score > self.away_score:
            return self.home_team
        if self.away_score > self.home_score:
            return self.away_team
        return None

    @property
    def is_draw(self):
        return (self.status == 'completed'
                and self.home_score is not None
                and self.home_score == self.away_score)


class Lineup(models.Model):
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='lineups')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='lineups')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='lineups')
    is_starting = models.BooleanField(default=True)
    shirt_number = models.IntegerField(null=True, blank=True)
    position = models.CharField(max_length=20, blank=True)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)
    minutes_played = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['fixture', '-is_starting', 'shirt_number']
        unique_together = [('fixture', 'player')]

    def __str__(self):
        return f'{self.player.full_name} — {self.fixture}'


class SportsEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('training', 'Training Session'),
        ('friendly', 'Friendly Match'),
        ('sports_day', 'Sports Day'),
        ('tournament', 'Tournament'),
        ('meet', 'Athletics Meet'),
        ('social', 'Social / Awards'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, default='training')
    sport = models.ForeignKey(Sport, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events')
    description = models.TextField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=255)
    cover_image = models.ImageField(upload_to='sports/events/', blank=True, null=True)
    registration_open = models.BooleanField(default=True)
    max_participants = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-starts_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            i = 2
            while SportsEvent.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_past(self):
        return self.starts_at < timezone.now()


class SportsNews(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    excerpt = models.CharField(max_length=500, blank=True)
    content = models.TextField()
    cover_image = models.ImageField(upload_to='sports/news/', blank=True, null=True)
    related_sport = models.ForeignKey(Sport, on_delete=models.SET_NULL, null=True, blank=True)
    related_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True)
    published = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']
        verbose_name_plural = 'Sports news'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            i = 2
            while SportsNews.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
