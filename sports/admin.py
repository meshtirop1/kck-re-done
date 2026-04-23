from django.contrib import admin
from .models import (
    Sport, Team, Player, Competition, Fixture, Lineup,
    SportsEvent, SportsNews,
)


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'active', 'sort_order')
    list_filter = ('category', 'active')
    list_editable = ('sort_order', 'active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    fields = ('jersey_number', 'full_name', 'position', 'is_captain', 'is_active')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport', 'short_name', 'captain', 'home_venue', 'active')
    list_filter = ('sport', 'active')
    search_fields = ('name', 'short_name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PlayerInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'team', 'jersey_number', 'position', 'is_captain', 'is_active')
    list_filter = ('team', 'position', 'is_captain', 'is_active')
    search_fields = ('full_name',)


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport', 'competition_type', 'season', 'start_date', 'end_date', 'active')
    list_filter = ('sport', 'competition_type', 'active', 'season')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('teams',)


class LineupInline(admin.TabularInline):
    model = Lineup
    extra = 0
    fields = ('team', 'player', 'is_starting', 'shirt_number', 'position', 'goals',
              'assists', 'yellow_cards', 'red_cards', 'minutes_played')


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'competition', 'kickoff', 'venue', 'status', 'home_score', 'away_score')
    list_filter = ('status', 'competition', 'kickoff')
    search_fields = ('home_team__name', 'away_team__name', 'venue')
    date_hierarchy = 'kickoff'
    inlines = [LineupInline]
    fieldsets = (
        ('Match', {'fields': ('competition', 'home_team', 'away_team', 'kickoff', 'venue', 'status')}),
        ('Result', {'fields': ('home_score', 'away_score', 'mvp', 'match_report', 'highlights_video_url')}),
        ('Admin', {'fields': ('notes', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SportsEvent)
class SportsEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'sport', 'starts_at', 'venue', 'registration_open', 'active')
    list_filter = ('event_type', 'sport', 'active', 'registration_open')
    search_fields = ('title', 'venue')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'starts_at'


@admin.register(SportsNews)
class SportsNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'related_sport', 'related_team', 'published', 'featured', 'published_at')
    list_filter = ('published', 'featured', 'related_sport')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
