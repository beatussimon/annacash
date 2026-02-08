"""
Balancing app configuration.
"""
from django.apps import AppConfig


class BalancingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'balancing'
    verbose_name = 'Balancing'
