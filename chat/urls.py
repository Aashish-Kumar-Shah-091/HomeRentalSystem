from django.urls import path

from . import views

urlpatterns = [
    path("<int:booking_id>/", views.chat_room, name="chat_room"),
    path("<int:booking_id>/upload-image/", views.upload_chat_image, name="chat_upload_image"),
]
