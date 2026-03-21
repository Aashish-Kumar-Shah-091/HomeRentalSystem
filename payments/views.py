from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from django.shortcuts import render
from django.utils import timezone

from home.models import Booking
from .models import Transaction
from .services import (
    decode_and_verify_esewa_response,
    generate_esewa_payment_data,
    is_verified_amount,
)

DEFAULT_PRODUCT_NAME = "Room Booking"
DEFAULT_AMOUNT = Decimal("1000.00")


def _coerce_amount(raw_amount):
    try:
        amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None

    if amount <= 0:
        return None

    return amount


def _build_checkout_context(*, form_data=None, error_message="", product_name=None, amount=None, booking_id=None):
    return {
        "form_data": form_data or {},
        "error_message": error_message,
        "product_name": product_name or DEFAULT_PRODUCT_NAME,
        "amount": amount if amount is not None else DEFAULT_AMOUNT,
        "booking_id": booking_id,
    }


def _parse_transaction_uuid(raw_value):
    try:
        return UUID(str(raw_value))
    except (TypeError, ValueError, AttributeError):
        return None


def _parse_booking_id(raw_value):
    try:
        booking_id = int(raw_value)
    except (TypeError, ValueError):
        return None

    return booking_id if booking_id > 0 else None


def _get_checkout_booking(request, raw_booking_id):
    booking_id = _parse_booking_id(raw_booking_id)
    if not booking_id or not request.user.is_authenticated:
        return None

    return (
        Booking.objects.select_related("property", "owner", "booked_by")
        .filter(
            pk=booking_id,
            booked_by=request.user,
            status=Booking.Status.ACCEPTED,
        )
        .first()
    )


def initiate_payment(request):
    source = request.POST if request.method == "POST" else request.GET
    booking = _get_checkout_booking(request, source.get("booking_id"))
    if booking:
        product_name = f"Booking Payment - {booking.property.title}"
        amount = booking.property.price.quantize(Decimal("0.01"))
        booking_id = booking.id
    else:
        product_name = (source.get("product_name") or DEFAULT_PRODUCT_NAME).strip() or DEFAULT_PRODUCT_NAME
        amount = _coerce_amount(source.get("amount") or DEFAULT_AMOUNT) or DEFAULT_AMOUNT
        booking_id = _parse_booking_id(source.get("booking_id"))

    if request.method == "POST":
        form_data = {
            "name": (request.POST.get("name") or "").strip(),
            "email": (request.POST.get("email") or "").strip(),
            "phone": (request.POST.get("phone") or "").strip(),
        }

        if not all(form_data.values()):
            return render(
                request,
                "payments/checkout.html",
                _build_checkout_context(
                    form_data=form_data,
                    error_message="Please fill in your name, email, and phone number.",
                    product_name=product_name,
                    amount=amount,
                    booking_id=booking_id,
                ),
                status=400,
            )

        transaction = Transaction.objects.create(
            customer_name=form_data["name"],
            customer_email=form_data["email"],
            customer_phone=form_data["phone"],
            product_name=product_name,
            product_id=uuid4(),
            amount=amount,
            booking=booking,
            payment_gateway=Transaction.PaymentGateway.ESEWA,
            status=Transaction.Status.PENDING,
        )
        payment_data = generate_esewa_payment_data(transaction)
        return render(
            request,
            "payments/esewa_form.html",
            {
                "payment_data": payment_data,
                "transaction": transaction,
            },
        )

    return render(
        request,
        "payments/checkout.html",
        _build_checkout_context(
            product_name=product_name,
            amount=amount,
            booking_id=booking_id,
        ),
    )


def payment_success(request):
    decoded_data = decode_and_verify_esewa_response(request.GET.get("data"))
    if not decoded_data:
        return render(
            request,
            "payments/failure.html",
            {
                "error_message": "We could not verify the eSewa payment response.",
            },
            status=400,
        )

    product_id = _parse_transaction_uuid(decoded_data.get("transaction_uuid"))
    if not product_id:
        return render(
            request,
            "payments/failure.html",
            {
                "error_message": "The payment response did not include a valid transaction ID.",
            },
            status=400,
        )

    transaction = Transaction.objects.filter(
        product_id=product_id,
        payment_gateway=Transaction.PaymentGateway.ESEWA,
    ).first()
    if not transaction:
        return render(
            request,
            "payments/failure.html",
            {
                "error_message": "Transaction not found for this payment response.",
            },
            status=404,
        )

    if not is_verified_amount(decoded_data, transaction.amount):
        return render(
            request,
            "payments/failure.html",
            {
                "transaction": transaction,
                "error_message": "Payment amount verification failed.",
            },
            status=400,
        )

    update_fields = []
    if transaction.status != Transaction.Status.COMPLETED:
        transaction.status = Transaction.Status.COMPLETED
        update_fields.append("status")

    if transaction.completed_at is None:
        transaction.completed_at = timezone.now()
        update_fields.append("completed_at")

    if transaction.booking_id and transaction.owner_is_read:
        transaction.owner_is_read = False
        update_fields.append("owner_is_read")

    if update_fields:
        transaction.save(update_fields=update_fields)

    return render(
        request,
        "payments/success.html",
        {
            "transaction": transaction,
            "gateway_response": decoded_data,
        },
    )


def payment_failure(request):
    transaction = None
    product_id = _parse_transaction_uuid(request.GET.get("transaction_uuid"))
    if product_id:
        transaction = Transaction.objects.filter(
            product_id=product_id,
            payment_gateway=Transaction.PaymentGateway.ESEWA,
        ).first()
        if transaction and transaction.status == Transaction.Status.PENDING:
            transaction.status = Transaction.Status.FAILED
            transaction.save(update_fields=["status"])

    return render(
        request,
        "payments/failure.html",
        {
            "transaction": transaction,
        },
    )
