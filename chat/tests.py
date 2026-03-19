from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse

from chat.models import ChatMessage
from chat.services import create_chat_message_for_user
from home.context_processors import unread_notifications_count
from home.models import Booking, BookingAcceptanceNotification, Property

User = get_user_model()
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff"
    b"\xff?\x00\x05\xfe\x02\xfeA\xdd\x94\x9b\x00\x00\x00\x00IEND\xaeB`\x82"
)


class BookingChatAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.tenant = User.objects.create_user(username="tenant", password="testpass123")
        self.outsider = User.objects.create_user(username="outsider", password="testpass123")
        self.property = Property.objects.create(
            user=self.owner,
            title="City Apartment",
            description="A clean rental property for testing.",
            price="25000.00",
            location="Kathmandu",
            property_type="rent",
            image=SimpleUploadedFile(
                "property.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
        )

    def create_booking(self, *, status):
        booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=status,
            is_accepted=status == Booking.Status.ACCEPTED,
        )
        return booking

    def test_chat_room_requires_accepted_booking_for_participants(self):
        booking = self.create_booking(status=Booking.Status.PENDING)
        self.client.login(username="tenant", password="testpass123")

        response = self.client.get(reverse("chat_room", args=[booking.id]))

        self.assertEqual(response.status_code, 403)

    def test_chat_room_allows_owner_and_tenant_after_acceptance(self):
        booking = self.create_booking(status=Booking.Status.ACCEPTED)
        chat_url = reverse("chat_room", args=[booking.id])

        self.client.login(username="tenant", password="testpass123")
        tenant_response = self.client.get(chat_url)
        self.assertEqual(tenant_response.status_code, 200)

        self.client.logout()
        self.client.login(username="owner", password="testpass123")
        owner_response = self.client.get(chat_url)
        self.assertEqual(owner_response.status_code, 200)

    def test_chat_room_blocks_unrelated_users(self):
        booking = self.create_booking(status=Booking.Status.ACCEPTED)
        self.client.login(username="outsider", password="testpass123")

        response = self.client.get(reverse("chat_room", args=[booking.id]))

        self.assertEqual(response.status_code, 403)


class NotificationChatVisibilityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.tenant = User.objects.create_user(username="tenant", password="testpass123")
        self.property = Property.objects.create(
            user=self.owner,
            title="Garden Flat",
            description="Notification visibility test property.",
            price="18000.00",
            location="Pokhara",
            property_type="rent",
            image=SimpleUploadedFile(
                "property.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
        )

    def test_notifications_hide_chat_for_pending_booking(self):
        booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=Booking.Status.PENDING,
        )
        self.client.login(username="owner", password="testpass123")

        response = self.client.get(reverse("notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("chat_room", args=[booking.id]))

    def test_notifications_hide_chat_when_accepted_booking_is_later_rejected(self):
        booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=Booking.Status.ACCEPTED,
            is_accepted=True,
        )
        BookingAcceptanceNotification.objects.create(
            property=self.property,
            booking=booking,
            tenant=self.tenant,
            owner=self.owner,
        )

        self.client.login(username="tenant", password="testpass123")
        accepted_response = self.client.get(reverse("notifications"))
        self.assertContains(accepted_response, reverse("chat_room", args=[booking.id]))

        booking.mark_rejected()
        booking.save(update_fields=["status", "is_accepted"])

        rejected_response = self.client.get(reverse("notifications"))
        self.assertNotContains(rejected_response, reverse("chat_room", args=[booking.id]))


class ChatMessageServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.tenant = User.objects.create_user(username="tenant", password="testpass123")
        self.outsider = User.objects.create_user(username="outsider", password="testpass123")
        self.property = Property.objects.create(
            user=self.owner,
            title="Riverside Home",
            description="Service-level chat test property.",
            price="32000.00",
            location="Lalitpur",
            property_type="rent",
            image=SimpleUploadedFile(
                "property.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
        )

    def test_create_chat_message_requires_accepted_booking(self):
        booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=Booking.Status.PENDING,
        )

        payload = create_chat_message_for_user(
            booking_id=booking.id,
            user_id=self.tenant.id,
            content="Hello from a pending booking",
        )

        self.assertIsNone(payload)
        self.assertFalse(ChatMessage.objects.exists())

    def test_create_chat_message_blocks_unrelated_users(self):
        booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=Booking.Status.ACCEPTED,
            is_accepted=True,
        )

        payload = create_chat_message_for_user(
            booking_id=booking.id,
            user_id=self.outsider.id,
            content="I should not be in this room",
        )

        self.assertIsNone(payload)
        self.assertFalse(ChatMessage.objects.exists())

    def test_create_chat_message_allows_accepted_booking_participants(self):
        booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=Booking.Status.ACCEPTED,
            is_accepted=True,
        )

        payload = create_chat_message_for_user(
            booking_id=booking.id,
            user_id=self.tenant.id,
            content="Hello owner",
        )

        self.assertIsNotNone(payload)
        self.assertEqual(payload["booking_id"], booking.id)
        self.assertEqual(payload["sender_id"], self.tenant.id)
        self.assertEqual(payload["content"], "Hello owner")
        self.assertEqual(ChatMessage.objects.count(), 1)

    def test_create_chat_message_allows_image_only_for_accepted_participants(self):
        booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=Booking.Status.ACCEPTED,
            is_accepted=True,
        )

        payload = create_chat_message_for_user(
            booking_id=booking.id,
            user_id=self.tenant.id,
            image_file=SimpleUploadedFile(
                "chat.png",
                PNG_BYTES,
                content_type="image/png",
            ),
        )

        self.assertIsNotNone(payload)
        self.assertTrue(payload["has_image"])
        self.assertTrue(payload["image_url"])
        self.assertEqual(payload["preview"], "Photo")
        self.assertEqual(ChatMessage.objects.count(), 1)


class ChatImageUploadTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.tenant = User.objects.create_user(username="tenant", password="testpass123")
        self.outsider = User.objects.create_user(username="outsider", password="testpass123")
        self.property = Property.objects.create(
            user=self.owner,
            title="Lake View Home",
            description="Image upload chat test property.",
            price="35000.00",
            location="Pokhara",
            property_type="rent",
            image=SimpleUploadedFile(
                "property.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
        )
        self.booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=Booking.Status.ACCEPTED,
            is_accepted=True,
        )

    def test_upload_chat_image_creates_chat_message(self):
        self.client.login(username="tenant", password="testpass123")

        response = self.client.post(
            reverse("chat_upload_image", args=[self.booking.id]),
            {
                "content": "See this photo",
                "image": SimpleUploadedFile(
                    "chat.png",
                    PNG_BYTES,
                    content_type="image/png",
                ),
            },
        )

        payload = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["content"], "See this photo")
        self.assertTrue(payload["has_image"])
        self.assertTrue(payload["image_url"])
        self.assertEqual(ChatMessage.objects.count(), 1)

    def test_upload_chat_image_rejects_invalid_file_type(self):
        self.client.login(username="tenant", password="testpass123")

        response = self.client.post(
            reverse("chat_upload_image", args=[self.booking.id]),
            {
                "image": SimpleUploadedFile(
                    "notes.txt",
                    b"plain-text",
                    content_type="text/plain",
                ),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Only JPG, PNG, GIF, and WEBP images are allowed.",
        )
        self.assertFalse(ChatMessage.objects.exists())

    def test_upload_chat_image_blocks_unrelated_users(self):
        self.client.login(username="outsider", password="testpass123")

        response = self.client.post(
            reverse("chat_upload_image", args=[self.booking.id]),
            {
                "image": SimpleUploadedFile(
                    "chat.png",
                    PNG_BYTES,
                    content_type="image/png",
                ),
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ChatMessage.objects.exists())


class ChatUnreadStateTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.tenant = User.objects.create_user(username="tenant", password="testpass123")
        self.property = Property.objects.create(
            user=self.owner,
            title="Hilltop Stay",
            description="Unread chat state property.",
            price="29000.00",
            location="Bhaktapur",
            property_type="rent",
            image=SimpleUploadedFile(
                "property.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
        )
        self.booking = Booking.objects.create(
            property=self.property,
            booked_by=self.tenant,
            owner=self.owner,
            status=Booking.Status.ACCEPTED,
            is_accepted=True,
        )

    def test_context_processor_exposes_unread_chat_count_and_recent_link(self):
        ChatMessage.objects.create(
            booking=self.booking,
            sender=self.owner,
            content="Are you still interested?",
        )

        request = self.factory.get("/")
        request.user = self.tenant

        context = unread_notifications_count(request)

        self.assertEqual(context["unread_chat_count"], 1)
        self.assertEqual(len(context["recent_chats"]), 1)
        self.assertEqual(
            context["recent_chats"][0]["url"],
            reverse("chat_room", args=[self.booking.id]),
        )
        self.assertTrue(context["recent_chats"][0]["is_unread"])

    def test_opening_chat_room_marks_incoming_messages_as_read(self):
        message = ChatMessage.objects.create(
            booking=self.booking,
            sender=self.owner,
            content="Please confirm your arrival time.",
        )

        self.client.login(username="tenant", password="testpass123")
        response = self.client.get(reverse("chat_room", args=[self.booking.id]))

        message.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message.is_read)

    def test_context_processor_uses_photo_preview_for_image_only_messages(self):
        ChatMessage.objects.create(
            booking=self.booking,
            sender=self.owner,
            image=SimpleUploadedFile(
                "chat.png",
                PNG_BYTES,
                content_type="image/png",
            ),
        )

        request = self.factory.get("/")
        request.user = self.tenant

        context = unread_notifications_count(request)

        self.assertEqual(context["recent_chats"][0]["preview"], "Photo")
