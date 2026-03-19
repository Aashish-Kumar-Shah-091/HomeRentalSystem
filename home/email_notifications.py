import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)


def _display_name(user) -> str:
    full_name = (getattr(user, "get_full_name", lambda: "")() or "").strip()
    username = (getattr(user, "username", "") or "").strip()
    return full_name or username or "there"


def _format_dt(dt) -> str:
    if not dt:
        return "—"
    try:
        return timezone.localtime(dt).strftime("%b %d, %Y %H:%M")
    except Exception:
        return str(dt)


def _abs_url(request, path: str) -> str:
    if request is None:
        return path
    try:
        return request.build_absolute_uri(path)
    except Exception:
        return path


def _property_urls(request, property_id: int) -> tuple[str, str]:
    property_path = reverse("property_detail", args=[property_id])
    properties_path = reverse("properties")
    return _abs_url(request, property_path), _abs_url(request, properties_path)


def _send_email(*, to_email: str, subject: str, html_template: str, text_template: str, context: dict) -> bool:
    if not to_email:
        logger.info("Skipping email send: missing recipient email (subject=%s)", subject)
        return False

    try:
        text_body = render_to_string(text_template, context).strip()
        html_body = render_to_string(html_template, context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Failed to send email (subject=%s, to=%s)", subject, to_email)
        return False


def _common_context(request, booking, *, status: str) -> dict:
    prop = booking.property
    customer = booking.booked_by
    owner = booking.owner

    property_url, properties_url = _property_urls(request, prop.id)

    owner_contact_name = (prop.contact_name or "").strip() or _display_name(owner)
    owner_contact_phone = (prop.contact_phone or "").strip()
    if not owner_contact_phone:
        owner_profile = getattr(owner, "profile", None)
        owner_contact_phone = (getattr(owner_profile, "phone_number", "") or "").strip()
    owner_contact_email = (prop.contact_email or "").strip() or (owner.email or "")

    return {
        "site_name": "Ghar Setu",
        "customer_name": _display_name(customer),
        "to_email": customer.email,
        "booking_id": booking.id,
        "booking_status": status,
        "booking_date": _format_dt(getattr(booking, "booked_at", None)),
        "property_title": prop.title,
        "property_location": prop.location,
        "property_type": getattr(prop, "get_property_type_display", lambda: prop.property_type)(),
        "total_amount": f"Rs. {prop.price}",
        "property_url": property_url,
        "properties_url": properties_url,
        "owner_contact_name": owner_contact_name or "—",
        "owner_contact_phone": owner_contact_phone or "—",
        "owner_contact_email": owner_contact_email or "—",
    }


def send_booking_confirmation_email(request, booking) -> bool:
    ctx = _common_context(request, booking, status="Pending acceptance")
    return _send_email(
        to_email=ctx["to_email"],
        subject="Booking Confirmation",
        html_template="emails/booking_confirmation.html",
        text_template="emails/booking_confirmation.txt",
        context=ctx,
    )


def send_booking_accepted_email(request, booking) -> bool:
    ctx = _common_context(request, booking, status="Accepted")
    ctx["accepted_date"] = _format_dt(timezone.now())
    return _send_email(
        to_email=ctx["to_email"],
        subject="Your Booking Has Been Accepted",
        html_template="emails/booking_accepted.html",
        text_template="emails/booking_accepted.txt",
        context=ctx,
    )


def send_booking_canceled_email(
    request,
    booking,
    *,
    cancellation_reason: str,
    refund_details: str,
) -> bool:
    ctx = _common_context(request, booking, status="Canceled")
    ctx["canceled_date"] = _format_dt(timezone.now())
    ctx["cancellation_reason"] = cancellation_reason or "Booking canceled."
    ctx["refund_details"] = refund_details or "No refund information available."
    return _send_email(
        to_email=ctx["to_email"],
        subject="Booking Cancellation",
        html_template="emails/booking_canceled.html",
        text_template="emails/booking_canceled.txt",
        context=ctx,
    )

