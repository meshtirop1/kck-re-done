from django.urls import path
from . import views

app_name = 'market'

urlpatterns = [
    # Public browse
    path('', views.market_home, name='home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('seller/<slug:slug>/', views.seller_detail, name='seller_detail'),

    # Member (authenticated)
    path('apply/', views.apply_to_sell, name='apply'),
    path('my-application/', views.my_application, name='my_application'),
    path('dashboard/', views.seller_dashboard, name='dashboard'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<slug:slug>/edit/', views.product_edit, name='product_edit'),
    path('products/<slug:slug>/delete/', views.product_delete, name='product_delete'),
    path('products/<slug:slug>/toggle/', views.product_toggle, name='product_toggle'),

    # Leader approval
    path('review/', views.leader_queue, name='leader_queue'),
    path('review/<int:pk>/', views.leader_review, name='leader_review'),
    path('sellers/', views.leader_all_sellers, name='leader_all_sellers'),
]
