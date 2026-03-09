"""
Django Admin Configuration
Registers models with Django admin panel for easy management.
"""

from django.contrib import admin
from .models import home, Testimonial

# Register your models here.
# These models will appear in the Django admin panel for database management

admin.site.register(home)  # Register legacy home model for admin management
admin.site.register(Testimonial)  # Register testimonials for admin moderation
