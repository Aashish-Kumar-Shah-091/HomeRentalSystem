from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "sender", "is_read", "created_at", "short_content")
    list_filter = ("is_read", "created_at")
    search_fields = (
        "content",
        "sender__username",
        "booking__property__title",
    )
    readonly_fields = ("created_at",)

    def short_content(self, obj):
        text = (obj.content or "").strip()
        return text[:60] + ("..." if len(text) > 60 else "")

    short_content.short_description = "Message"
