"""
URL patterns for audit app.
"""
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('reports/', views.audit_reports, name='reports'),
    path('log/', views.audit_log, name='log'),
    path('alerts/', views.audit_alerts, name='alerts'),
]
