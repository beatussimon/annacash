"""
URL patterns for mchezo app.

Provides real backend routing for all mchezo operations.
"""
from django.urls import path
from . import views

app_name = 'mchezo'

urlpatterns = [
    # Member management
    path('<int:group_id>/members/', views.MchezoMemberListView.as_view(), name='members'),
    path('<int:group_id>/members/add/', views.MchezoMemberAddView.as_view(), name='add_member'),
    path('<int:group_id>/members/<int:membership_id>/', views.mchezo_member_detail, name='member_detail'),
    path('<int:group_id>/members/<int:membership_id>/edit/', views.MchezoMemberEditView.as_view(), name='edit_member'),
    
    # Cycle management
    path('<int:group_id>/cycle/start/', views.MchezoCycleStartView.as_view(), name='cycle_start'),
    path('<int:group_id>/cycle/close/', views.MchezoCycleCloseView.as_view(), name='cycle_close'),
    
    # Contribution and payout
    path('<int:group_id>/contribution/create/', views.MchezoContributionCreateView.as_view(), name='contribution_create'),
    path('<int:group_id>/payout/create/', views.MchezoPayoutCreateView.as_view(), name='payout_create'),
    path('<int:group_id>/payout/<int:payout_id>/edit/', views.MchezoPayoutUpdateView.as_view(), name='payout_edit'),
    
    # Settings
    path('<int:group_id>/settings/', views.mchezo_group_settings, name='settings'),
]
