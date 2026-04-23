from django.urls import path
from . import views

app_name = 'sports'

urlpatterns = [
    path('', views.home, name='home'),

    # Fixtures & Results
    path('fixtures/', views.fixture_list, name='fixture_list'),
    path('fixtures/<int:pk>/', views.fixture_detail, name='fixture_detail'),
    path('results/', views.fixture_list, {'status': 'results'}, name='results'),

    # Teams
    path('teams/', views.team_list, name='team_list'),
    path('teams/<slug:slug>/', views.team_detail, name='team_detail'),

    # Competitions
    path('competitions/', views.competition_list, name='competition_list'),
    path('competitions/<slug:slug>/', views.competition_detail, name='competition_detail'),

    # Sports (categories)
    path('sports/', views.sport_list, name='sport_list'),
    path('sports/<slug:slug>/', views.sport_detail, name='sport_detail'),

    # Events
    path('events/', views.event_list, name='event_list'),
    path('events/<slug:slug>/', views.event_detail, name='event_detail'),

    # News
    path('news/', views.news_list, name='news_list'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
]
