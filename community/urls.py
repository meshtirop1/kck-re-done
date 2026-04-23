from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.community_index, name='index'),
    path('history/', views.community_history, name='history'),
    path('location/', views.community_location, name='location'),
    path('hours/', views.community_hours, name='hours'),
    path('mission/', views.community_mission, name='mission'),
    path('vision/', views.community_vision, name='vision'),
    path('news/', views.news_list, name='news_list'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
]
