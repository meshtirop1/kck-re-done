from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('', views.certificate_verify_home, name='verify_home'),
    path('verify/<uuid:code>/', views.certificate_verify, name='verify'),
    path('my/', views.my_certificates, name='my_certificates'),
    path('<int:pk>/', views.certificate_detail, name='detail'),
    path('<int:pk>/download/', views.certificate_download, name='download'),
    # Management (leaders/admins only)
    path('manage/', views.certificate_manage_list, name='manage_list'),
    path('manage/new/', views.certificate_create, name='create'),
    path('manage/<int:pk>/', views.certificate_manage_detail, name='manage_detail'),
    path('manage/<int:pk>/publish/', views.certificate_publish, name='publish'),
]
