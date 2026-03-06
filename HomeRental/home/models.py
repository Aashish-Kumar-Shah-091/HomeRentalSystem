from django.db import models
from django.contrib.auth.models import User

class home(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=200)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Property(models.Model):
    PROPERTY_TYPE = (
        ('rent', 'Rent'),
        ('sell', 'Sell'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=120, blank=True, default="")
    contact_phone = models.CharField(max_length=30, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    property_type = models.CharField(max_length=10, choices=PROPERTY_TYPE)
    image = models.ImageField(upload_to='property_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "property")

    def __str__(self):
        return f"{self.user.username} saved {self.property.title}"


class Booking(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner_bookings")
    booked_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.booked_by.username} - {self.property.title}"


class BookingCancellationNotification(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cancellation_notifications",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_cancellation_notifications",
    )
    canceled_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.owner.username} canceled booking for {self.tenant.username}"


class BookingAcceptanceNotification(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="acceptance_notifications",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_acceptance_notifications",
    )
    accepted_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.owner.username} accepted booking for {self.tenant.username}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to="profile_images/", blank=True, null=True)

    def __str__(self):
        return self.user.username


class Testimonial(models.Model):
    ROLE_CHOICES = (
        ("tenant", "Tenant"),
        ("owner", "Property Owner"),
    )
    RATING_CHOICES = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="testimonials")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    message = models.TextField(max_length=400)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
