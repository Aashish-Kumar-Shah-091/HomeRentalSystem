# sendemail/utils.py

from django.core.mail import send_mail
from django.conf import settings

def send_booking_email(user_email, subject, message):
    """
    Sends an email using Django's send_mail function.
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )