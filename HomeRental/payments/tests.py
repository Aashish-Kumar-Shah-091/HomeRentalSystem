import base64
import hashlib
import hmac
import json
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

from home.context_processors import unread_notifications_count
from home.models import Booking, Property
from .models import Transaction


class PaymentFlowTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @staticmethod
    def _create_accepted_booking():
        user_model = get_user_model()
        owner = user_model.objects.create_user(
            username=f"owner_{uuid4().hex[:8]}",
            password="pass1234",
        )
        tenant = user_model.objects.create_user(
            username=f"tenant_{uuid4().hex[:8]}",
            password="pass1234",
            email="tenant@example.com",
        )

        property_obj = Property.objects.create(
            user=owner,
            title="Test Apartment",
            description="Spacious apartment for testing payments.",
            price=Decimal("1500.00"),
            location="Kathmandu",
            property_type="rent",
            image=SimpleUploadedFile(
                name="property.jpg",
                content=b"property-image-bytes",
                content_type="image/jpeg",
            ),
        )

        booking = Booking.objects.create(
            property=property_obj,
            booked_by=tenant,
            owner=owner,
            status=Booking.Status.ACCEPTED,
            is_accepted=True,
            is_read=True,
        )
        return booking, tenant, owner

    @staticmethod
    def _sign_payload(payload, signed_field_names):
        fields = [field.strip() for field in signed_field_names.split(",") if field.strip()]
        message = ",".join(f"{field}={payload[field]}" for field in fields)
        digest = hmac.new(
            settings.ESEWA_SECRET_KEY.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    @staticmethod
    def _encode_gateway_payload(payload):
        return base64.b64encode(
            json.dumps(payload).encode("utf-8")
        ).decode("utf-8")

    def _build_signed_gateway_payload(self, **kwargs):
        payload = {
            "signed_field_names": "transaction_code,status,total_amount,transaction_uuid,product_code,signed_field_names",
            **kwargs,
        }
        payload["signature"] = self._sign_payload(payload, payload["signed_field_names"])
        return payload

    def test_checkout_page_renders(self):
        response = self.client.get(reverse("payments:checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Checkout With eSewa")

    def test_initiate_payment_creates_pending_transaction(self):
        response = self.client.post(
            reverse("payments:checkout"),
            {
                "name": "Ram Shah",
                "email": "ram@example.com",
                "phone": "9800000000",
                "product_name": "Room Booking",
                "amount": "1000.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payments/esewa_form.html")
        self.assertIn("signature", response.context["payment_data"])
        self.assertIn("signed_field_names", response.context["payment_data"])

        transaction = Transaction.objects.get()
        self.assertEqual(transaction.customer_name, "Ram Shah")
        self.assertEqual(transaction.customer_email, "ram@example.com")
        self.assertEqual(transaction.customer_phone, "9800000000")
        self.assertEqual(transaction.status, Transaction.Status.PENDING)
        self.assertEqual(transaction.payment_gateway, Transaction.PaymentGateway.ESEWA)

    def test_initiate_payment_attaches_booking_and_uses_booking_amount(self):
        booking, tenant, _owner = self._create_accepted_booking()
        self.client.force_login(tenant)

        response = self.client.post(
            reverse("payments:checkout"),
            {
                "name": "Tenant User",
                "email": "tenant@example.com",
                "phone": "9800000000",
                "booking_id": str(booking.id),
                "product_name": "Tampered Product Name",
                "amount": "1.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get()
        self.assertEqual(transaction.booking_id, booking.id)
        self.assertEqual(transaction.amount, booking.property.price)
        self.assertEqual(
            transaction.product_name,
            f"Booking Payment - {booking.property.title}",
        )
        self.assertTrue(transaction.owner_is_read)

    def test_payment_success_marks_transaction_completed(self):
        transaction = Transaction.objects.create(
            customer_name="Sita Rai",
            customer_email="sita@example.com",
            customer_phone="9811111111",
            product_name="Room Booking",
            product_id=uuid4(),
            amount=Decimal("1000.00"),
            payment_gateway=Transaction.PaymentGateway.ESEWA,
            status=Transaction.Status.PENDING,
        )

        payload = self._build_signed_gateway_payload(
            transaction_uuid=str(transaction.product_id),
            product_code="EPAYTEST",
            status="COMPLETE",
            total_amount="1000.00",
            transaction_code="TEST123",
        )
        encoded_data = self._encode_gateway_payload(payload)

        response = self.client.get(
            reverse("payments:success"),
            {"data": encoded_data},
        )

        transaction.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(transaction.status, Transaction.Status.COMPLETED)

    def test_payment_success_creates_unread_owner_notification_for_booking(self):
        booking, tenant, owner = self._create_accepted_booking()
        transaction = Transaction.objects.create(
            customer_name=tenant.get_full_name() or tenant.username,
            customer_email=tenant.email or "tenant@example.com",
            customer_phone="9811111111",
            product_name=f"Booking Payment - {booking.property.title}",
            product_id=uuid4(),
            amount=booking.property.price,
            booking=booking,
            payment_gateway=Transaction.PaymentGateway.ESEWA,
            status=Transaction.Status.PENDING,
            owner_is_read=True,
        )

        payload = self._build_signed_gateway_payload(
            transaction_uuid=str(transaction.product_id),
            product_code="EPAYTEST",
            status="COMPLETE",
            total_amount=str(booking.property.price),
            transaction_code="TESTOWNER1",
        )
        encoded_data = self._encode_gateway_payload(payload)

        response = self.client.get(
            reverse("payments:success"),
            {"data": encoded_data},
        )

        transaction.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(transaction.status, Transaction.Status.COMPLETED)
        self.assertFalse(transaction.owner_is_read)
        self.assertIsNotNone(transaction.completed_at)

        request = self.factory.get("/")
        request.user = owner
        context = unread_notifications_count(request)

        self.assertGreaterEqual(context["unread_notifications_count"], 1)
        self.assertTrue(
            any(item["kind"] == "payment_received" for item in context["recent_notifications"])
        )

    def test_payment_success_rejects_amount_mismatch(self):
        transaction = Transaction.objects.create(
            customer_name="Nabin Karki",
            customer_email="nabin@example.com",
            customer_phone="9833333333",
            product_name="Room Booking",
            product_id=uuid4(),
            amount=Decimal("1000.00"),
            payment_gateway=Transaction.PaymentGateway.ESEWA,
            status=Transaction.Status.PENDING,
        )

        payload = self._build_signed_gateway_payload(
            transaction_uuid=str(transaction.product_id),
            product_code="EPAYTEST",
            status="COMPLETE",
            total_amount="900.00",
            transaction_code="TEST124",
        )
        encoded_data = self._encode_gateway_payload(payload)

        response = self.client.get(
            reverse("payments:success"),
            {"data": encoded_data},
        )

        transaction.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(transaction.status, Transaction.Status.PENDING)

    def test_payment_success_rejects_invalid_status(self):
        transaction = Transaction.objects.create(
            customer_name="Rina Maharjan",
            customer_email="rina@example.com",
            customer_phone="9844444444",
            product_name="Room Booking",
            product_id=uuid4(),
            amount=Decimal("1000.00"),
            payment_gateway=Transaction.PaymentGateway.ESEWA,
            status=Transaction.Status.PENDING,
        )

        payload = self._build_signed_gateway_payload(
            transaction_uuid=str(transaction.product_id),
            product_code="EPAYTEST",
            status="PENDING",
            total_amount="1000.00",
            transaction_code="TEST125",
        )
        encoded_data = self._encode_gateway_payload(payload)

        response = self.client.get(
            reverse("payments:success"),
            {"data": encoded_data},
        )

        transaction.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(transaction.status, Transaction.Status.PENDING)

    def test_payment_failure_marks_pending_transaction_failed(self):
        transaction = Transaction.objects.create(
            customer_name="Hari Lama",
            customer_email="hari@example.com",
            customer_phone="9822222222",
            product_name="Room Booking",
            product_id=uuid4(),
            amount=Decimal("1000.00"),
            payment_gateway=Transaction.PaymentGateway.ESEWA,
            status=Transaction.Status.PENDING,
        )

        response = self.client.get(
            reverse("payments:failure"),
            {"transaction_uuid": str(transaction.product_id)},
        )

        transaction.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(transaction.status, Transaction.Status.FAILED)
