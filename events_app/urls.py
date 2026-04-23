from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('calendar/', views.event_calendar, name='calendar'),
    path('highlights/', views.event_highlights, name='highlights'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),
    path('<slug:slug>/register/', views.event_register, name='event_register'),
    path('<slug:slug>/cancel/', views.event_cancel_registration, name='event_cancel'),
]
