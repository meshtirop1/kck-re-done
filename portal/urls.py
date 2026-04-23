from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('site-settings/', views.site_settings, name='site_settings'),
    path('<str:key>/', views.generic_list, name='list'),
    path('<str:key>/new/', views.generic_create, name='create'),
    path('<str:key>/<int:pk>/edit/', views.generic_edit, name='edit'),
    path('<str:key>/<int:pk>/delete/', views.generic_delete, name='delete'),
]
