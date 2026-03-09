"""
WSGI Configuration for HomeRental Project

Exposes the WSGI callable as a module-level variable named 'application'.
This is used by production web servers (Gunicorn, uWSGI, etc.) to run the Django application.

WSGI (Web Server Gateway Interface) is the Python standard for web applications.

For more information, see:
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Set the Django settings module to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomeRental.settings')

# Get the WSGI application - this is what web servers call to handle requests
application = get_wsgi_application()
