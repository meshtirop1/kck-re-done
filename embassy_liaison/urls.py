from django.urls import path
from . import views

app_name = 'embassy_liaison'

urlpatterns = [
    # Public info
    path('', views.liaison_info, name='info'),
    path('services/', views.service_guide_list, name='service_list'),
    path('services/<str:service_type>/', views.service_guide_detail, name='service_detail'),

    # Member flows
    path('request/new/', views.request_create, name='request_create'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('request/<int:pk>/', views.my_request_detail, name='my_request_detail'),
    path('request/<int:pk>/cancel/', views.request_cancel, name='request_cancel'),
    path('request/<int:pk>/document/<str:doc>/', views.document_download, name='document_download'),

    # Officer portal
    path('officer/', views.officer_dashboard, name='officer_dashboard'),
    path('officer/requests/', views.officer_request_list, name='officer_request_list'),
    path('officer/request/<int:pk>/', views.officer_request_detail, name='officer_request_detail'),
]
