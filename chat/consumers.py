import json
from json import JSONDecodeError

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .services import create_chat_message_for_user, get_chat_booking_for_user_id, room_name_for_booking


class BookingChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.booking_id = self.scope["url_route"]["kwargs"]["booking_id"]
        # Keep the websocket room name aligned with the shared chat helpers.
        self.group_name = room_name_for_booking(self.booking_id)

        has_access = await self.user_has_chat_access()
        if not has_access:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data is not None or text_data is None:
            await self.send_error("Binary messages are not supported.")
            return

        try:
            data = json.loads(text_data)
        except JSONDecodeError:
            await self.send_error("Invalid chat payload.")
            return

        content = (data.get("content") or data.get("message") or "").strip()
        if not content:
            await self.send_error("Message cannot be empty.")
            return

        if len(content) > 1000:
            await self.send_error("Message must be 1000 characters or fewer.")
            return

        user = self.scope["user"]
        message = await database_sync_to_async(create_chat_message_for_user)(
            booking_id=self.booking_id,
            user_id=getattr(user, "id", None),
            content=content,
        )
        if not message:
            await self.send_error(
                "Chat is only available to the tenant and owner while the booking is accepted."
            )
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": message,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def send_error(self, message):
        # Keep error payloads explicit so the frontend can show useful feedback.
        await self.send(text_data=json.dumps({"error": message}))

    @database_sync_to_async
    def user_has_chat_access(self):
        return bool(
            get_chat_booking_for_user_id(
                user_id=getattr(self.scope.get("user"), "id", None),
                booking_id=self.booking_id,
            )
        )
