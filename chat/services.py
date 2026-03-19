import os

from django.core.exceptions import PermissionDenied
from django.core.files.images import get_image_dimensions
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from home.models import Booking

from .models import ChatMessage

CHAT_IMAGE_MAX_BYTES = 5 * 1024 * 1024
CHAT_IMAGE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def room_name_for_booking(booking_id):
    return f"booking_{booking_id}"


def user_can_access_booking_chat(user, booking):
    if not getattr(user, "is_authenticated", False):
        return False

    return booking.chat_enabled and user.id in {
        booking.booked_by_id,
        booking.owner_id,
    }


def get_chat_booking_queryset():
    return Booking.objects.select_related("property", "booked_by", "owner")


def get_chat_booking_for_user(user, booking_id):
    booking = get_object_or_404(get_chat_booking_queryset(), pk=booking_id)

    if not user_can_access_booking_chat(user, booking):
        raise PermissionDenied(
            "Chat is only available to the tenant and owner after the booking is accepted."
        )

    return booking


def get_chat_booking_for_user_id(*, user_id, booking_id):
    if not user_id:
        return None

    return (
        get_chat_booking_queryset()
        .filter(pk=booking_id, status=Booking.Status.ACCEPTED)
        .filter(Q(booked_by_id=user_id) | Q(owner_id=user_id))
        .first()
    )


def validate_chat_image(image_file):
    if not image_file:
        return "Please choose an image to send."

    if image_file.size > CHAT_IMAGE_MAX_BYTES:
        return "Image must be 5 MB or smaller."

    file_extension = os.path.splitext(image_file.name or "")[1].lower()
    if file_extension not in CHAT_IMAGE_ALLOWED_EXTENSIONS:
        return "Only JPG, PNG, GIF, and WEBP images are allowed."

    try:
        image_file.seek(0)
        get_image_dimensions(image_file)
        image_file.seek(0)
    except Exception:
        return "Please upload a valid image file."

    return ""


def image_message_preview():
    return "Photo"


def create_chat_message_for_user(*, booking_id, user_id, content="", image_file=None):
    content = (content or "").strip()
    if not content and not image_file:
        return None

    booking = get_chat_booking_for_user_id(user_id=user_id, booking_id=booking_id)
    if not booking:
        return None

    if image_file:
        image_error = validate_chat_image(image_file)
        if image_error:
            return None

    message = ChatMessage.objects.create(
        booking=booking,
        sender_id=user_id,
        content=content,
        image=image_file,
    )
    message = ChatMessage.objects.select_related("sender").get(pk=message.pk)
    return serialize_message(message)


def serialize_message(message):
    local_dt = timezone.localtime(message.created_at)
    image_url = ""
    if message.image:
        try:
            image_url = message.image.url
        except ValueError:
            image_url = ""

    preview = message.content or (image_message_preview() if image_url else "")

    return {
        "id": message.id,
        "booking_id": message.booking_id,
        "sender_id": message.sender_id,
        "sender_username": message.sender.username,
        "content": message.content,
        "preview": preview,
        "has_image": bool(image_url),
        "image_url": image_url,
        "image_name": os.path.basename(message.image.name) if message.image else "",
        "timestamp": local_dt.isoformat(),
        "timestamp_label": local_dt.strftime("%b %d, %Y %H:%M"),
    }
