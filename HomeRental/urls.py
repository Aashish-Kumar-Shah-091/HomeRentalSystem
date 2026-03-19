"""
URL Configuration for HomeRental Project

Main URL router for the entire application.
Routes user requests to appropriate URL configurations based on path.

The `urlpatterns` list routes URLs to views. For more information see:
https://docs.djangoproject.com/en/6.0/topics/http/urls/

URL Routing:
- Admin: /admin/ - Django admin panel
- Home App: / - All home rental app URLs
- Authentication: /accounts/ - Django built-in auth URLs (login, logout, password change, etc.)
- Media Files: /media/ - User-uploaded files (images, documents)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.urls import views as auth_views

# URL patterns for the entire application
urlpatterns = [
    # Admin panel for site management
    path('admin/', admin.site.urls),
    
    # All home rental app URLs (properties, bookings, notifications, etc.)
    path('', include('home.urls')),
    path('chat/', include('chat.urls')),
    
    # Django built-in authentication URLs (login, logout, password change, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

# Serve media files (user uploads) during development
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
