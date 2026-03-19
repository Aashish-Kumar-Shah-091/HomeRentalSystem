"""
URL Configuration for Home Rental App
Maps URL paths to corresponding view functions.
Organized by functionality: pages, homes, properties, bookings, notifications, user profiles.
"""

from django.urls import path
from . import views

# URL patterns for routing
urlpatterns = [
    # ===== PUBLIC PAGES =====
    path('', views.index, name='home_list'),  # Homepage with testimonials
    path('about/', views.about, name='about'),  # About page with company info
    path('help/', views.help_page, name='help'),  # Help/FAQ and contact page
    path('reviews/', views.reviews, name='reviews'),  # Reviews/testimonials page
    
    # ===== HOME LISTINGS (Legacy) =====
    path('home/', views.index, name='home'),  # Home page alternate route
    path('homes/', views.home_list, name='homes'),  # List all home entries
    path('create/', views.home_create, name='home_create'),  # Create new home entry
    path('<int:home_id>/edit/', views.home_edit, name='home_edit'),  # Edit home entry
    path('<int:home_id>/delete/', views.home_delete, name='home_delete'),  # Delete home entry
    
    # ===== USER AUTHENTICATION =====
    path('register/', views.register, name='register'),  # User registration page
    
    # ===== PROPERTY MANAGEMENT =====
    path('property/', views.add_property, name='property'),  # Add new property listing
    path('properties/', views.property_list, name='properties'),  # Display all properties with filters
    path('properties/mine/', views.my_properties, name='my_properties'),  # View properties listed by current user
    path('properties/others/', views.other_properties, name='other_properties'),  # View properties listed by others
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),  # View property details
    path('properties/<int:property_id>/edit/', views.property_edit, name='property_edit'),  # Edit property
    path('properties/<int:property_id>/delete/', views.property_delete, name='property_delete'),  # Delete property
    
    # ===== FAVORITES/BOOKMARKS =====
    path('properties/<int:property_id>/favorite-toggle/', views.toggle_favorite, name='toggle_favorite'),  # Add/remove favorite
    path('favorites/', views.favorite_list, name='favorite_list'),  # View saved properties
    
    # ===== BOOKING MANAGEMENT =====
    path('book/<int:property_id>/', views.book_property, name='book_property'),  # Book a property
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),  # Cancel a booking
    path('bookings/<int:booking_id>/accept/', views.accept_booking, name='accept_booking'),  # Accept a booking request
    
    # ===== NOTIFICATIONS =====
    path('notifications/', views.notifications, name='notifications'),  # View all notifications
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),  # Mark single notification as read
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),  # Mark all notifications as read
    
    # ===== USER PROFILES =====
    path('tenants/<int:user_id>/', views.tenant_profile, name='tenant_profile'),  # View tenant profile (owner only)
    path('profile/', views.profile, name='profile'),  # View/edit own user profile
] 
