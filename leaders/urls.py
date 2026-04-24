from django.urls import path
from . import views, role_views

app_name = 'leaders'

urlpatterns = [
    path('', views.leaders_list, name='list'),
    path('<int:pk>/', views.leader_detail, name='detail'),

    # Role / permission management — President + superuser only
    path('manage/roles/', role_views.roles_overview, name='roles_overview'),
    path('manage/roles/<int:pk>/', role_views.role_edit, name='role_edit'),
    path('manage/roles/<int:pk>/reset/', role_views.role_reset_defaults, name='role_reset_defaults'),
    path('manage/roles/audit/', role_views.role_audit_log, name='role_audit'),
]
