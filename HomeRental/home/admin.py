"""
Django Admin Configuration
Registers models with Django admin panel for easy management.
"""

from django.contrib import admin
from .models import home, Property, Testimonial


@admin.register(home)
class HomeAdmin(admin.ModelAdmin):
    """Admin controls for legacy home listings."""
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__username", "text")
    ordering = ("-created_at",)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin controls for property listings."""
    list_display = ("id", "title", "user", "location", "price", "property_type", "created_at")
    list_filter = ("property_type", "created_at")
    search_fields = ("title", "location", "contact_name", "contact_email", "user__username")
    list_select_related = ("user",)
    ordering = ("-created_at",)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin controls for testimonials."""
    list_display = ("id", "user", "role", "rating", "created_at")
    list_filter = ("role", "rating", "created_at")
    search_fields = ("user__username", "message")
    ordering = ("-created_at",)
