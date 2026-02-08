"""
URL patterns for dashboard app.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.HomepageView.as_view(), name='home'),
    path('app-switcher/', views.AppSwitcherView.as_view(), name='app_switcher'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('superadmin/', views.AdminDashboardView.as_view(), name='admin'),
    path('wakala/<int:wakala_id>/', views.WakalaDashboardView.as_view(), name='wakala'),
    path('mchezo/<int:group_id>/', views.MchezoDashboardView.as_view(), name='mchezo'),
]
