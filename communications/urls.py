from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    path('', views.communications_public_list, name='public_list'),
    path('letter/<int:pk>/', views.communication_detail, name='detail'),
    path('letter/<int:pk>/download/', views.communication_download, name='download'),
    path('announcements/', views.announcements_list, name='announcements'),
    path('announcements/<slug:slug>/', views.announcement_detail, name='announcement_detail'),
    path('inbox/', views.my_inbox, name='inbox'),
    # Management
    path('manage/', views.manage_communications_list, name='manage_list'),
    path('manage/new/', views.communication_create, name='create'),
    path('manage/<int:pk>/', views.manage_communication_detail, name='manage_detail'),
    path('manage/<int:pk>/edit/', views.communication_edit, name='edit'),
    path('manage/<int:pk>/publish/', views.communication_publish, name='publish'),
    path('manage/announcements/', views.manage_announcements_list, name='manage_announcements'),
    path('manage/announcements/new/', views.announcement_create, name='announcement_create'),
    path('manage/announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('manage/announcements/<int:pk>/publish/', views.announcement_publish, name='announcement_publish'),
]
