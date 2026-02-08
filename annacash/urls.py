"""
URL configuration for ANNA project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('dashboard.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('core/', include('core.urls', namespace='core')),
    path('wakala/', include('wakala.urls', namespace='wakala')),
    path('mchezo/', include('mchezo.urls', namespace='mchezo')),
    path('config/', include('config.urls', namespace='config')),
    path('audit/', include('audit.urls', namespace='audit')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin site header
admin.site.site_header = 'ANNA - Financial Operations Platform'
admin.site.site_title = 'ANNA'
admin.site.index_title = 'Administration'
