from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from channels.layers import get_channel_layer

from .services import (
    create_chat_message_for_user,
    get_chat_booking_for_user,
    room_name_for_booking,
    validate_chat_image,
)


@login_required
def chat_room(request, booking_id):
    # Reuse the shared service so page access follows the same rules as websocket chat.
    booking = get_chat_booking_for_user(request.user, booking_id)
    # Opening the room marks incoming messages as read for the current participant.
    booking.chat_messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
    # Match the current model field name when loading message history.
    chat_messages = booking.chat_messages.select_related("sender")

    return render(
        request,
        "chat/chat_room.html",
        {
            "booking": booking,
            "chat_messages": chat_messages,
            "user_id": request.user.id,
        },
    )


@login_required
@require_POST
def upload_chat_image(request, booking_id):
    booking = get_chat_booking_for_user(request.user, booking_id)
    content = (request.POST.get("content") or "").strip()
    image_file = request.FILES.get("image")

    if not content and not image_file:
        return JsonResponse({"error": "Add a message or choose an image to send."}, status=400)

    if len(content) > 1000:
        return JsonResponse({"error": "Message must be 1000 characters or fewer."}, status=400)

    if image_file:
        image_error = validate_chat_image(image_file)
        if image_error:
            return JsonResponse({"error": image_error}, status=400)

    message = create_chat_message_for_user(
        booking_id=booking.id,
        user_id=request.user.id,
        content=content,
        image_file=image_file,
    )
    if not message:
        return JsonResponse({"error": "Unable to send this chat message."}, status=400)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room_name_for_booking(booking.id),
        {
            "type": "chat_message",
            "message": message,
        },
    )

    return JsonResponse(message, status=201)
