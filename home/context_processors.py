"""
Context Processors
Adds custom context data to all templates globally.
Used to display notification counts and recent notifications in navigation/header.
"""

from .models import (
    Booking,
    BookingCancellationNotification,
    BookingAcceptanceNotification,
)


def unread_notifications_count(request):
    """
    Context processor that calculates unread notification count and recent notifications.
    
    This function is called for every request and adds notification data to template context.
    It handles three types of notifications:
    1. Booking requests (tenants booking properties owned by current user)
    2. Booking cancellations (owners canceling bookings for current user)
    3. Booking acceptances (owners accepting current user's booking requests)
    
    Returns a dictionary with:
    - unread_notifications_count: Total count of unread notifications
    - recent_notifications: List of 5 most recent notifications with details
    """
    
    # If user is not logged in, return empty notification data
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "recent_notifications": [],
        }

    # ===== FETCH ALL NOTIFICATIONS FOR CURRENT USER =====
    
    # Notifications for property owners: when someone books their property
    owner_notifications = Booking.objects.filter(owner=request.user).select_related(
        "booked_by", "property"
    )
    
    # Notifications for tenants: when an owner cancels their booking
    tenant_notifications = BookingCancellationNotification.objects.filter(
        tenant=request.user
    ).select_related("owner", "property")
    
    # Notifications for tenants: when an owner accepts their booking
    tenant_acceptance = BookingAcceptanceNotification.objects.filter(
        tenant=request.user
    ).select_related("owner", "property")

    # ===== FORMAT OWNER NOTIFICATIONS =====
    owner_recent = [
        {
            "message": f"{item.booked_by.username} booked {item.property.title}",
            "url": f"/properties/{item.property.id}/?view=compact",
            "created_at": item.booked_at,
            "is_read": item.is_read,
        }
        for item in owner_notifications
    ]
    
    # ===== FORMAT TENANT CANCELLATION NOTIFICATIONS =====
    tenant_recent = [
        {
            "message": f"{item.owner.username} canceled your booking for {item.property.title}",
            "url": f"/properties/{item.property.id}/",
            "created_at": item.canceled_at,
            "is_read": item.is_read,
        }
        for item in tenant_notifications
    ]
    
    # ===== FORMAT TENANT ACCEPTANCE NOTIFICATIONS =====
    tenant_accepted_recent = [
        {
            "message": f"{item.owner.username} accepted your booking for {item.property.title}",
            "url": f"/properties/{item.property.id}/",
            "created_at": item.accepted_at,
            "is_read": item.is_read,
        }
        for item in tenant_acceptance
    ]

    # ===== COMBINE AND SORT NOTIFICATIONS =====
    # Merge all notification types and sort by date (newest first)
    recent = sorted(
        owner_recent + tenant_recent + tenant_accepted_recent,
        key=lambda n: n["created_at"],
        reverse=True,
    )[:5]  # Keep only 5 most recent notifications for display
    
    # Count total unread notifications across all types
    count = (
        owner_notifications.filter(is_read=False).count()
        + tenant_notifications.filter(is_read=False).count()
        + tenant_acceptance.filter(is_read=False).count()
    )

    # Return context data to be available in all templates
    return {
        "unread_notifications_count": count,  # Total unread count for badge display
        "recent_notifications": recent,  # List of recent notifications for dropdown
    }


