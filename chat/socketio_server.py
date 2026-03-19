from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import Q
import socketio

from home.models import Booking

from .models import ChatMessage
from .services import read_socket_token, room_name_for_booking, serialize_message

User = get_user_model()

sio = socketio.AsyncServer(async_mode="asgi")


@sync_to_async
def resolve_socket_session(token):
    payload = read_socket_token(token)
    if not payload:
        return None

    booking = (
        Booking.objects.select_related("booked_by", "owner")
        .filter(pk=payload.get("booking_id"), status=Booking.Status.ACCEPTED)
        .first()
    )
    if not booking:
        return None

    user = User.objects.filter(pk=payload.get("user_id"), is_active=True).first()
    if not user:
        return None

    if user.id not in {booking.booked_by_id, booking.owner_id}:
        return None

    return {
        "user_id": user.id,
        "username": user.username,
        "booking_id": booking.id,
        "room_name": room_name_for_booking(booking.id),
    }


@sync_to_async
def booking_is_chat_accessible(*, booking_id, user_id):
    return Booking.objects.filter(
        pk=booking_id,
        status=Booking.Status.ACCEPTED,
    ).filter(
        Q(booked_by_id=user_id) | Q(owner_id=user_id)
    ).exists()


@sync_to_async
def create_chat_message(*, booking_id, user_id, content):
    if not Booking.objects.filter(
        pk=booking_id,
        status=Booking.Status.ACCEPTED,
    ).filter(
        Q(booked_by_id=user_id) | Q(owner_id=user_id)
    ).exists():
        return None

    message = ChatMessage.objects.create(
        booking_id=booking_id,
        sender_id=user_id,
        content=content,
    )
    message = ChatMessage.objects.select_related("sender").get(pk=message.pk)
    return serialize_message(message)


@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    session_data = await resolve_socket_session(token)

    if not session_data:
        raise ConnectionRefusedError("Unauthorized chat session.")

    await sio.save_session(sid, session_data)


@sio.event
async def join_room(sid, data):
    session = await sio.get_session(sid)
    booking_id = int((data or {}).get("booking_id") or 0)

    if not session or booking_id != session["booking_id"]:
        await sio.emit("chat_error", {"message": "Invalid room request."}, to=sid)
        return

    has_access = await booking_is_chat_accessible(
        booking_id=booking_id,
        user_id=session["user_id"],
    )
    if not has_access:
        await sio.emit(
            "chat_error",
            {"message": "You no longer have access to this chat."},
            to=sid,
        )
        await sio.disconnect(sid)
        return

    await sio.enter_room(sid, session["room_name"])
    await sio.emit(
        "room_joined",
        {
            "booking_id": booking_id,
            "room_name": session["room_name"],
        },
        to=sid,
    )


@sio.event
async def send_message(sid, data):
    session = await sio.get_session(sid)
    booking_id = int((data or {}).get("booking_id") or 0)
    content = ((data or {}).get("message") or "").strip()

    if not session or booking_id != session["booking_id"]:
        await sio.emit("chat_error", {"message": "Invalid booking."}, to=sid)
        return

    if not content:
        await sio.emit("chat_error", {"message": "Message cannot be empty."}, to=sid)
        return

    if len(content) > 1000:
        await sio.emit(
            "chat_error",
            {"message": "Message must be 1000 characters or fewer."},
            to=sid,
        )
        return

    message = await create_chat_message(
        booking_id=booking_id,
        user_id=session["user_id"],
        content=content,
    )
    if not message:
        await sio.emit(
            "chat_error",
            {"message": "Unable to send message for this booking."},
            to=sid,
        )
        return

    await sio.emit("receive_message", message, room=session["room_name"])


@sio.event
async def disconnect(sid):
    return None
