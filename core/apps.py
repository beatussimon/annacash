"""
Core app configuration.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        # Import templatetags to register them
        try:
            from core import templatetags
        except ImportError:
            pass
