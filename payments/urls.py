from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("checkout/", views.initiate_payment, name="checkout"),
    path("success/", views.payment_success, name="success"),
    path("failure/", views.payment_failure, name="failure"),
]
