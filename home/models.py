"""
Home Rental System Models
This module defines all database models for the home rental application.
Models include Property listings, User Profiles, Bookings, Favorites, and Testimonials.
"""

import builtins

from django.db import models
from django.contrib.auth.models import User

# Legacy model for home listings (may be deprecated)
class home(models.Model):
    """
    Legacy home model for storing home-related content.
    This model stores user-submitted home information with photos.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User who created the home entry
    text = models.TextField(max_length=200)  # Description or text content
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)  # Home photo storage
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-timestamp on creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-timestamp on updates


class Property(models.Model):
    """
    Property model represents rental properties listed on the platform.
    Stores property details, contact information, location (with coordinates), and media.
    """
    # Property type choices: rent or sell
    PROPERTY_TYPE = (
        ('rent', 'Rent'),
        ('sell', 'Sell'),
    )
    
    # Foreign key to User - property owner
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Basic property information
    title = models.CharField(max_length=200)  # Property title/name
    description = models.TextField()  # Detailed property description
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Rental/selling price
    location = models.CharField(max_length=200)  # Property location (street/area)
    
    # Contact information for property owner
    contact_name = models.CharField(max_length=120, blank=True, default="")
    contact_phone = models.CharField(max_length=30, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    
    # Property classification
    property_type = models.CharField(max_length=10, choices=PROPERTY_TYPE)  # Rent or Sell
    
    # Media and location coordinates
    image = models.ImageField(upload_to='property_images/')  # Property main image
    created_at = models.DateTimeField(auto_now_add=True)  # Creation timestamp
    latitude = models.FloatField(null=True, blank=True)  # GPS latitude for map display
    longitude = models.FloatField(null=True, blank=True)  # GPS longitude for map display

    def __str__(self):
        """String representation returns property title"""
        return self.title

    @property
    def image_url(self):
        """
        Return a usable image URL only when the backing file exists.
        This prevents loading errors if the image file has been deleted.
        """
        if not self.image:
            return ""

        try:
            # Check if the image file actually exists in storage
            if self.image.storage.exists(self.image.name):
                return self.image.url
        except Exception:
            return ""

        return ""


class Favorite(models.Model):
    """
    Favorite model stores user favorites (bookmarks/saved properties).
    Each user can have multiple favorites, each favorite is unique per user-property pair.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")  # User who favorited
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="favorited_by")  # Favorited property
    created_at = models.DateTimeField(auto_now_add=True)  # When property was marked as favorite

    class Meta:
        # Ensure a user can only favorite a property once
        unique_together = ("user", "property")

    def __str__(self):
        return f"{self.user.username} saved {self.property.title}"


class Booking(models.Model):
    """
    Booking model represents a property booking request from a tenant to a property owner.
    Tracks booking status, acceptance, and read status for notifications.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    property = models.ForeignKey(Property, on_delete=models.CASCADE)  # Booked property
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")  # Tenant who booked
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner_bookings")  # Property owner
    booked_at = models.DateTimeField(auto_now_add=True)  # When the booking was made
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )  # Booking lifecycle status
    is_read = models.BooleanField(default=False)  # Whether owner has seen the booking
    is_accepted = models.BooleanField(default=False)  # Whether owner accepted the booking

    def __str__(self):
        return f"{self.booked_by.username} - {self.property.title}"

    @builtins.property
    def user(self):
        """Compatibility alias for the tenant field used by chat/business rules."""
        return self.booked_by

    @builtins.property
    def room_name(self):
        """Socket.IO room name for this booking conversation."""
        return f"booking_{self.pk}"

    @builtins.property
    def chat_enabled(self):
        """Chat becomes available only after a booking is accepted."""
        return self.status == self.Status.ACCEPTED

    def mark_pending(self):
        self.status = self.Status.PENDING
        self.is_accepted = False

    def mark_accepted(self):
        self.status = self.Status.ACCEPTED
        self.is_accepted = True

    def mark_rejected(self):
        self.status = self.Status.REJECTED
        self.is_accepted = False


class BookingCancellationNotification(models.Model):
    """
    Notification model for when owners cancel a booking.
    Records who canceled, which booking was canceled, and when.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE)  # The canceled property
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cancellation_notifications")  # Tenant who had booking canceled
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_cancellation_notifications")  # Owner who canceled
    canceled_at = models.DateTimeField(auto_now_add=True)  # When the cancellation was made
    is_read = models.BooleanField(default=False)  # Whether tenant has read the notification

    def __str__(self):
        return f"{self.owner.username} canceled booking for {self.tenant.username}"


class BookingAcceptanceNotification(models.Model):
    """
    Notification model for when owners accept a booking.
    Records who accepted, which booking was accepted, and when.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE)  # The accepted property
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="booking_acceptance_notifications",
        null=True,
        blank=True,
    )  # Accepted booking linked to chat access
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="acceptance_notifications")  # Tenant whose booking was accepted
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_acceptance_notifications")  # Owner who accepted
    accepted_at = models.DateTimeField(auto_now_add=True)  # When the booking was accepted
    is_read = models.BooleanField(default=False)  # Whether tenant has read the notification

    def __str__(self):
        return f"{self.owner.username} accepted booking for {self.tenant.username}"


class Profile(models.Model):
    """
    User Profile model extends Django's User model with additional user information.
    Stores profile-specific data like phone number and profile image.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")  # One-to-one link to User
    phone_number = models.CharField(max_length=20, blank=True)  # User's contact phone number
    image = models.ImageField(upload_to="profile_images/", blank=True, null=True)  # User's profile picture

    def __str__(self):
        return self.user.username


class Testimonial(models.Model):
    """
    Testimonial model stores user reviews and ratings for the platform.
    Users can provide feedback based on their experience as tenant or owner.
    """
    # User role when writing testimonial
    ROLE_CHOICES = (
        ("tenant", "Tenant"),
        ("owner", "Property Owner"),
    )
    
    # Numeric rating from 1 to 5 stars
    RATING_CHOICES = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="testimonials")  # User who wrote testimonial
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)  # Role of the user (tenant or owner)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)  # Star rating (1-5)
    message = models.TextField(max_length=400)  # Testimonial text/feedback
    created_at = models.DateTimeField(auto_now_add=True)  # When testimonial was created

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
