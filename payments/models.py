import uuid

from django.db import models


class Transaction(models.Model):
    class PaymentGateway(models.TextChoices):
        ESEWA = "esewa", "eSewa"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    product_name = models.CharField(max_length=200)
    product_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking = models.ForeignKey(
        "home.Booking",
        on_delete=models.SET_NULL,
        related_name="payment_transactions",
        null=True,
        blank=True,
    )
    payment_gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices,
        default=PaymentGateway.ESEWA,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner_is_read = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.product_name} ({self.product_id}) - {self.status}"
