"""
Root URL configuration for LIORA project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # App URLs
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('profile/', include('profile_app.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    # django-allauth (Google Login)
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
