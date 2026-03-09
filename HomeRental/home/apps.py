"""
App Configuration for Home Rental App

Django app configuration class that initializes the home rental application.
This is automatically detected by Django and loaded when the application starts.
"""

from django.apps import AppConfig


class HomeConfig(AppConfig):
    """
    Configuration class for the home rental application.
    
    Attributes:
        default_auto_field: Specifies the type of auto-generated primary key fields
        name: The name of the Django application/app label
    """
    # Use BigAutoField for model primary keys (supports more records)
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'  # App label used in database and migrations
