"""
URL patterns for wakala app.

Provides real backend routing for all wakala operations.
"""
from django.urls import path
from . import views

app_name = 'wakala'

urlpatterns = [
    # Wakala listing (admin)
    path('wakalas/', views.WakalaListView.as_view(), name='list'),
    
    # Transaction listing
    path('<int:wakala_id>/transactions/', views.WakalaTransactionListView.as_view(), name='transactions'),
    
    # Transaction CRUD
    path('<int:wakala_id>/transaction/create/', views.WakalaTransactionCreateView.as_view(), name='transaction_create'),
    path('<int:wakala_id>/transaction/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('<int:wakala_id>/transaction/<int:transaction_id>/edit/', views.WakalaTransactionEditView.as_view(), name='edit_transaction'),
    path('<int:wakala_id>/transaction/<int:transaction_id>/delete/', views.WakalaTransactionDeleteView.as_view(), name='delete_transaction'),
    
    # Financial day management
    path('<int:wakala_id>/day/open/', views.WakalaDayOpenView.as_view(), name='open_day'),
    path('<int:wakala_id>/day/close/', views.WakalaDayCloseView.as_view(), name='close_day'),
    
    # Settings
    path('<int:wakala_id>/settings/', views.wakala_settings, name='settings'),
]
