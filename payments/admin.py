from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "booking",
        "customer_email",
        "product_name",
        "product_id",
        "amount",
        "payment_gateway",
        "status",
        "owner_is_read",
        "completed_at",
    )
    list_filter = ("payment_gateway", "status", "owner_is_read")
    search_fields = (
        "customer_name",
        "customer_email",
        "customer_phone",
        "product_name",
        "product_id",
        "booking__property__title",
        "booking__booked_by__username",
        "booking__owner__username",
    )
