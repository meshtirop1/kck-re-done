from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('ambassador/', views.ambassador_profile, name='ambassador'),
    path('presidents-message/', views.presidents_message, name='presidents_message'),
    path('embassy-history/', views.embassy_history, name='embassy_history'),
    path('visit/', views.visit_us, name='visit'),
    path('discover/', views.discover_kenya, name='discover'),
    path('discover/attraction/<slug:slug>/', views.attraction_detail, name='attraction_detail'),
    path('search/', views.search, name='search'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('data-handling/', views.DataHandlingView.as_view(), name='data_handling'),
]
