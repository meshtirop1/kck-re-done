from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('visa/types/', views.visa_types, name='visa_types'),
    path('visa/type/<slug:slug>/', views.visa_type_detail, name='visa_type_detail'),
    path('visa/services/', views.visa_services, name='visa_services'),
    path('visa/issues/', views.visa_issues, name='visa_issues'),
    path('visa/faqs/', views.visa_faqs, name='visa_faqs'),
    path('visa/apply/', views.visa_apply, name='visa_apply'),
    path('visa/application/<int:pk>/', views.visa_application_detail, name='visa_application_detail'),
    path('passport/request/', views.passport_request, name='passport_request'),
    path('passport/apply/', views.passport_apply, name='passport_apply'),
    path('passport/application/<int:pk>/', views.passport_application_detail, name='passport_application_detail'),
    path('queries/', views.queries, name='queries'),
    path('highlights/', views.highlights, name='highlights'),
    path('faqs/', views.all_faqs, name='faqs'),
]
