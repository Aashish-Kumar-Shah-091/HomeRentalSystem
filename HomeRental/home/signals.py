from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from sendemail.utils import send_booking_email
from .models import Booking

@receiver(pre_save, sender=Booking)
def cache_previous_booking_status(sender, instance, **kwargs):
    """
    Cache the previous status so we only email on real status changes.
    """
    if not instance.pk:
        instance._previous_status = None
        return

    previous = sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    instance._previous_status = previous


@receiver(post_save, sender=Booking)
def send_booking_notification(sender, instance, created, **kwargs):
    """
    Send email when a booking is created or when its status changes.
    """
    property_name = instance.property.title
    tenant_name = instance.booked_by.first_name or instance.booked_by.username
    owner_name = instance.owner.first_name or instance.owner.username
    owner_email = (
        (instance.property.contact_email or "").strip()
        or (instance.owner.email or "").strip()
    )

    if created:
        if not owner_email:
            return

        subject = "New Booking Request"
        message = (
            f"Hello {owner_name},\n\n"
            f"You have received a new booking request from {tenant_name} "
            f"for your property {property_name}."
        )
        send_booking_email(owner_email, subject, message)
        return

    previous_status = getattr(instance, "_previous_status", None)
    if previous_status == instance.status:
        return

    if instance.status == Booking.Status.PENDING:
        if not owner_email:
            return

        subject = "New Booking Request"
        message = (
            f"Hello {owner_name},\n\n"
            f"You have received a new booking request from {tenant_name} "
            f"for your property {property_name}."
        )
        send_booking_email(owner_email, subject, message)
        return

    user_email = (instance.booked_by.email or "").strip()
    if not user_email:
        return

    if instance.status == Booking.Status.ACCEPTED:
        subject = "Booking Accepted"
        message = f"Hello {tenant_name},\n\nYour booking for {property_name} has been accepted!"
        send_booking_email(user_email, subject, message)
    elif instance.status == Booking.Status.REJECTED:
        subject = "Booking Rejected"
        message = f"Hello {tenant_name},\n\nYour booking for {property_name} has been rejected."
        send_booking_email(user_email, subject, message)
