from django.urls import path
from . import views

app_name = 'endorsements'

urlpatterns = [
    # Public verify
    path('', views.verify_home, name='verify_home'),
    path('verify/<uuid:code>/', views.verify, name='verify'),

    # Member view
    path('my/', views.my_endorsements, name='my_endorsements'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/download/', views.download, name='download'),

    # Officer / admin manage
    path('manage/', views.manage_list, name='manage_list'),
    path('manage/new/', views.create, name='create'),
    path('manage/<int:pk>/', views.manage_detail, name='manage_detail'),
    path('manage/<int:pk>/edit/', views.edit, name='edit'),
    path('manage/<int:pk>/publish/', views.publish, name='publish'),
    path('manage/<int:pk>/revoke/', views.revoke, name='revoke'),

    # Quick generate from an embassy service request
    path('manage/from-request/<int:request_id>/', views.create_from_request, name='create_from_request'),
]
