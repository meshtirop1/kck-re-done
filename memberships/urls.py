from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    # Public / member
    path('', views.membership_home, name='home'),
    path('apply/', views.membership_apply, name='apply'),
    path('my/<int:pk>/', views.my_membership, name='my_membership'),
    path('my/<int:pk>/declare-payment/', views.declare_payment, name='declare_payment'),
    path('my/<int:pk>/card.pdf', views.member_card_pdf, name='member_card_pdf'),
    path('verify/<str:member_number>/', views.verify_membership, name='verify'),

    # Treasurer dashboard
    path('treasurer/', views.treasurer_dashboard, name='treasurer_dashboard'),
    path('treasurer/queue/', views.treasurer_queue, name='treasurer_queue'),
    path('treasurer/audit-log/', views.treasurer_audit_log, name='treasurer_audit_log'),
    path('treasurer/tier/', views.treasurer_tier, name='treasurer_tier'),
    path('treasurer/bank-settings/', views.treasurer_bank_settings, name='treasurer_bank'),
    path('treasurer/bank-import/', views.treasurer_bank_import, name='treasurer_bank_import'),
    path('treasurer/benefits/', views.treasurer_benefits, name='treasurer_benefits'),
    path('treasurer/benefits/new/', views.treasurer_benefit_edit, name='treasurer_benefit_new'),
    path('treasurer/benefits/<int:pk>/edit/', views.treasurer_benefit_edit, name='treasurer_benefit_edit'),
    path('treasurer/benefits/<int:pk>/delete/', views.treasurer_benefit_delete, name='treasurer_benefit_delete'),
    path('treasurer/<int:pk>/', views.treasurer_detail, name='treasurer_detail'),

    # President / oversight (read-only)
    path('oversight/', views.oversight_dashboard, name='oversight_dashboard'),
    path('oversight/audit/', views.oversight_audit_log, name='oversight_audit'),
    path('oversight/members/', views.oversight_members, name='oversight_members'),
    path('oversight/export.csv', views.oversight_export_csv, name='oversight_export_csv'),
]
