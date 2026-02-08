"""
Wakala app configuration.
"""
from django.apps import AppConfig


class WakalaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wakala'
    verbose_name = 'Wakala Management'
