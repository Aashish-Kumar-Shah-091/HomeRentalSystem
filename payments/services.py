import base64
import binascii
import hashlib
import hmac
import json
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote, urlencode

from django.conf import settings

ESEWA_TEST_FORM_URL = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
ESEWA_SUCCESS_STATUSES = {"COMPLETE", "COMPLETED", "SUCCESS"}
ESEWA_SIGNED_FIELD_NAMES = "total_amount,transaction_uuid,product_code"


def _format_amount(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid payment amount.") from exc

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    return format(amount, ".2f")


def _build_failure_url(transaction):
    base_url = settings.FAILURE_URL
    query = urlencode({"transaction_uuid": str(transaction.product_id)})
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


def _get_secret_key():
    return getattr(settings, "ESEWA_SECRET_KEY", "8gBm/:&EnhH.1/q")


def _normalize_signed_field_names(signed_field_names):
    if not signed_field_names:
        return []

    return [field.strip() for field in str(signed_field_names).split(",") if field.strip()]


def _build_signature_message(payload, signed_fields):
    parts = []
    for field in signed_fields:
        if field not in payload:
            return None
        parts.append(f"{field}={payload[field]}")
    return ",".join(parts)


def _generate_hmac_signature(message, secret_key):
    digest = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def _verify_payload_signature(payload):
    signature = str(payload.get("signature", "")).strip()
    signed_field_names = payload.get("signed_field_names")
    signed_fields = _normalize_signed_field_names(signed_field_names)
    if not signature or not signed_fields:
        return False

    message = _build_signature_message(payload, signed_fields)
    if message is None:
        return False

    expected_signature = _generate_hmac_signature(message, _get_secret_key())
    return hmac.compare_digest(signature, expected_signature)


def _decode_base64_json_payload(encoded_data):
    if not encoded_data:
        return None

    normalized_data = unquote(str(encoded_data)).strip()
    normalized_data = normalized_data.replace(" ", "+")
    if not normalized_data:
        return None

    # eSewa callbacks can occasionally omit padding; normalize before decode.
    normalized_data += "=" * (-len(normalized_data) % 4)

    decoders = (
        lambda value: base64.b64decode(value, validate=True),
        base64.urlsafe_b64decode,
    )
    for decoder in decoders:
        try:
            decoded_text = decoder(normalized_data).decode("utf-8")
            return json.loads(decoded_text)
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            continue

    return None


def generate_esewa_payment_data(transaction):
    amount = _format_amount(transaction.amount)
    payment_data = {
        "gateway_url": getattr(settings, "ESEWA_FORM_URL", ESEWA_TEST_FORM_URL),
        "amount": amount,
        "tax_amount": "0.00",
        "total_amount": amount,
        "transaction_uuid": str(transaction.product_id),
        "product_code": settings.ESEWA_MERCHANT_ID,
        "product_service_charge": "0.00",
        "product_delivery_charge": "0.00",
        "success_url": settings.SUCCESS_URL,
        "failure_url": _build_failure_url(transaction),
    }

    signed_field_names = getattr(settings, "ESEWA_SIGNED_FIELD_NAMES", ESEWA_SIGNED_FIELD_NAMES)
    signed_fields = _normalize_signed_field_names(signed_field_names)
    message = _build_signature_message(payment_data, signed_fields)
    if message is None:
        raise ValueError("Signed fields are missing in payment payload.")

    payment_data["signed_field_names"] = ",".join(signed_fields)
    payment_data["signature"] = _generate_hmac_signature(message, _get_secret_key())
    return payment_data


def decode_and_verify_esewa_response(encoded_data):
    payload = _decode_base64_json_payload(encoded_data)
    if not payload:
        return None

    transaction_uuid = payload.get("transaction_uuid")
    if not transaction_uuid:
        return None

    product_code = payload.get("product_code")
    if not product_code or product_code != settings.ESEWA_MERCHANT_ID:
        return None

    status = str(payload.get("status", "")).upper()
    if status not in ESEWA_SUCCESS_STATUSES:
        return None

    if not _verify_payload_signature(payload):
        return None

    return payload


def is_verified_amount(payload, expected_amount):
    raw_amount = payload.get("total_amount") or payload.get("amount")
    if raw_amount is None:
        return False

    try:
        callback_amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"))
        expected = Decimal(str(expected_amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return False

    return callback_amount == expected


get_esewa_payment_data = generate_esewa_payment_data
verify_esewa_payment = decode_and_verify_esewa_response
