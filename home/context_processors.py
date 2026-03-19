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
from django.db.models import Q
from django.urls import reverse

from chat.services import image_message_preview

NOTIFICATION_META = {
    "booking_request": {
        "accent": "primary",
        "icon": "fa-calendar-plus",
        "type_label": "Booking request",
    },
    "booking_canceled": {
        "accent": "danger",
        "icon": "fa-circle-xmark",
        "type_label": "Canceled",
    },
    "booking_accepted": {
        "accent": "success",
        "icon": "fa-circle-check",
        "type_label": "Accepted",
    },
}

ACCEPTED_CHAT_NOTIFICATION_MESSAGE = "Your booking has been accepted. You can now chat with the owner."


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
            "unread_chat_count": 0,
            "recent_chats": [],
        }

    # ===== FETCH NOTIFICATIONS FOR CURRENT USER =====

    owner_unread_count = Booking.objects.filter(
        owner=request.user,
        is_read=False,
    ).exclude(
        status=Booking.Status.REJECTED,
    ).count()
    tenant_canceled_unread_count = BookingCancellationNotification.objects.filter(
        tenant=request.user, is_read=False
    ).count()
    tenant_accepted_unread_count = BookingAcceptanceNotification.objects.filter(
        tenant=request.user, is_read=False
    ).count()

    from chat.models import ChatMessage

    recent_chat_messages_qs = (
        ChatMessage.objects.filter(
            booking__status=Booking.Status.ACCEPTED,
        )
        .filter(Q(booking__booked_by=request.user) | Q(booking__owner=request.user))
        .select_related("booking__property", "booking__booked_by", "booking__owner", "sender")
        .order_by("-created_at", "-id")
    )
    unread_chat_count = recent_chat_messages_qs.exclude(sender=request.user).filter(
        is_read=False
    ).count()

    # Notifications for property owners: when someone books their property
    owner_recent_qs = (
        Booking.objects.filter(owner=request.user)
        .exclude(status=Booking.Status.REJECTED)
        .select_related("booked_by", "property")
        .order_by("-booked_at")[:10]
    )

    # Notifications for tenants: when an owner cancels their booking
    tenant_canceled_recent_qs = (
        BookingCancellationNotification.objects.filter(tenant=request.user)
        .select_related("owner", "property")
        .order_by("-canceled_at")[:10]
    )

    # Notifications for tenants: when an owner accepts their booking
    tenant_accepted_recent_qs = (
        BookingAcceptanceNotification.objects.filter(tenant=request.user)
        .select_related("owner", "property")
        .order_by("-accepted_at")[:10]
    )

    # ===== FORMAT OWNER NOTIFICATIONS =====
    owner_recent = [
        {
            "kind": "booking_request",
            "message": f"{item.booked_by.username} booked {item.property.title}",
            "url": f"/properties/{item.property.id}/?view=compact",
            "created_at": item.booked_at,
            "is_read": item.is_read,
            **NOTIFICATION_META["booking_request"],
        }
        for item in owner_recent_qs
    ]
    
    # ===== FORMAT TENANT CANCELLATION NOTIFICATIONS =====
    tenant_recent = [
        {
            "kind": "booking_canceled",
            "message": f"{item.owner.username} canceled your booking for {item.property.title}",
            "url": f"/properties/{item.property.id}/",
            "created_at": item.canceled_at,
            "is_read": item.is_read,
            **NOTIFICATION_META["booking_canceled"],
        }
        for item in tenant_canceled_recent_qs
    ]
    
    # ===== FORMAT TENANT ACCEPTANCE NOTIFICATIONS =====
    tenant_accepted_recent = [
        {
            "kind": "booking_accepted",
            "message": ACCEPTED_CHAT_NOTIFICATION_MESSAGE,
            "url": reverse("notifications"),
            "created_at": item.accepted_at,
            "is_read": item.is_read,
            **NOTIFICATION_META["booking_accepted"],
        }
        for item in tenant_accepted_recent_qs
    ]

    # ===== COMBINE AND SORT NOTIFICATIONS =====
    # Merge all notification types and sort by date (newest first)
    recent = sorted(
        owner_recent + tenant_recent + tenant_accepted_recent,
        key=lambda n: n["created_at"],
        reverse=True,
    )[:5]  # Keep only 5 most recent notifications for display

    recent_chats = []
    seen_booking_ids = set()
    for item in recent_chat_messages_qs[:25]:
        if item.booking_id in seen_booking_ids:
            continue

        seen_booking_ids.add(item.booking_id)
        counterpart = (
            item.booking.owner
            if item.booking.booked_by_id == request.user.id
            else item.booking.booked_by
        )
        recent_chats.append(
            {
                "booking_id": item.booking_id,
                "url": reverse("chat_room", args=[item.booking_id]),
                "counterpart_name": counterpart.username,
                "property_title": item.booking.property.title,
                "preview": item.content or (image_message_preview() if item.image else ""),
                "created_at": item.created_at,
                "is_unread": item.sender_id != request.user.id and not item.is_read,
            }
        )
        if len(recent_chats) == 5:
            break
    
    # Count total unread notifications across all types
    count = owner_unread_count + tenant_canceled_unread_count + tenant_accepted_unread_count

    # Return context data to be available in all templates
    return {
        "unread_notifications_count": count,  # Total unread count for badge display
        "recent_notifications": recent,  # List of recent notifications for dropdown
        "unread_chat_count": unread_chat_count,
        "recent_chats": recent_chats,
    }
