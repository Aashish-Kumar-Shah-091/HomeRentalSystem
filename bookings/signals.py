import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Booking

logger = logging.getLogger(__name__)


def _display_name(user) -> str:
    full_name = (getattr(user, "get_full_name", lambda: "")() or "").strip()
    username = (getattr(user, "username", "") or "").strip()
    return full_name or username or "Unknown user"


def _format_booked_at(booked_at) -> str:
    if not booked_at:
        return "N/A"

    try:
        return timezone.localtime(booked_at).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(booked_at)


def _owner_recipient(booking: Booking) -> str:
    return (booking.owner.email or "").strip() or (booking.property.contact_email or "").strip()


def _booking_details(booking: Booking) -> list[str]:
    return [
        f"Booking ID: {booking.pk}",
        f"Property: {booking.property.title}",
        f"Location: {booking.property.location}",
        f"Tenant: {_display_name(booking.user)}",
        f"Tenant Email: {booking.user.email or 'N/A'}",
        f"Owner: {_display_name(booking.owner)}",
        f"Booked At: {_format_booked_at(booking.booked_at)}",
        f"Status: {booking.get_status_display()}",
    ]


def _send_booking_email(*, subject: str, message: str, recipient: str) -> bool:
    if not recipient:
        logger.warning("Skipping booking email because recipient is missing (subject=%s).", subject)
        return False

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[recipient],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Failed to send booking email (subject=%s, recipient=%s).", subject, recipient)
        return False


def _send_new_booking_email(booking: Booking) -> bool:
    message = "\n".join(
        [
            f'A new booking request was created for "{booking.property.title}".',
            "",
            *_booking_details(booking),
        ]
    )
    return _send_booking_email(
        subject="New Booking Request",
        message=message,
        recipient=_owner_recipient(booking),
    )


def _send_status_email(booking: Booking) -> bool:
    if booking.status == Booking.Status.ACCEPTED:
        subject = "Booking Accepted"
        intro = f'Your booking request for "{booking.property.title}" has been accepted.'
    elif booking.status == Booking.Status.REJECTED:
        subject = "Booking Rejected"
        intro = f'Your booking request for "{booking.property.title}" has been rejected.'
    else:
        return False

    message = "\n".join([intro, "", *_booking_details(booking)])
    return _send_booking_email(
        subject=subject,
        message=message,
        recipient=(booking.user.email or "").strip(),
    )


@receiver(pre_save, sender=Booking)
def store_previous_booking_status(sender, instance: Booking, **kwargs):
    instance._previous_status = None
    if not instance.pk:
        return

    instance._previous_status = (
        sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    )


@receiver(post_save, sender=Booking)
def send_booking_notifications(sender, instance: Booking, created: bool, **kwargs):
    def _notify():
        if created:
            _send_new_booking_email(instance)
            return

        previous_status = getattr(instance, "_previous_status", None)
        if previous_status == instance.status:
            return

        _send_status_email(instance)

    transaction.on_commit(_notify)
