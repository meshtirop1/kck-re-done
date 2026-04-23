from django.urls import path
from . import views

app_name = 'leaders'

urlpatterns = [
    path('', views.leaders_list, name='list'),
    path('<int:pk>/', views.leader_detail, name='detail'),
]
