"""
Forms Configuration
Defines all form classes used in the application for data input and validation.
Includes forms for user registration, property listing, profile updates, and testimonials.
"""

from django import forms 
from .models import home, Property, Profile, Testimonial
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class homeForm(forms.ModelForm):
    """
    Form for home entries (legacy).
    Allows users to add text and photos for home listings.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap form-control class to all fields
        for field in self.fields.values():
            if isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs["class"] = "form-control"
            else:
                field.widget.attrs["class"] = "form-control"

    class Meta:
        model = home
        fields = ['text', 'photo']  # Allow editing text and photo


class UserRegistrationForm(forms.Form):
    """
    Custom user registration form.
    Validates username uniqueness and password strength.
    """
    username = forms.CharField(max_length=150, strip=False, help_text="")
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, strip=False)  # Password field
    password2 = forms.CharField(widget=forms.PasswordInput, strip=False)  # Password confirmation field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            # Disable password autocomplete for security
            if "password" in field_name:
                field.widget.attrs["autocomplete"] = "new-password"

    def clean_username(self):
        """
        Validate that username doesn't already exist in database.
        Prevents duplicate user accounts.
        """
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username

    def clean(self):
        """
        Validate password matching and password strength.
        Ensures both passwords are identical and meet Django requirements.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Check if passwords match
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two password fields didn't match.")

        # Validate password strength against Django validators
        if password1:
            user = User(
                username=cleaned_data.get("username", ""),
                email=cleaned_data.get("email", ""),
            )
            try:
                validate_password(password1, user=user)
            except ValidationError as exc:
                self.add_error("password1", exc)

        return cleaned_data

    def save(self):
        """
        Create and return new user with provided credentials.
        Should only be called after form validation passes.
        """
        return User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )


class PropertyForm(forms.ModelForm):
    """
    Form for creating and editing property listings.
    Collects property details, location, contact info, and images.
    """
    COORDINATE_LOCATION_RE = re.compile(r"^\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*$")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to all fields
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            # Add helpful placeholder text for contact fields
            if name == "contact_name":
                field.widget.attrs["placeholder"] = "Contact person"
            if name == "contact_phone":
                field.widget.attrs["placeholder"] = "Phone number"
            if name == "contact_email":
                field.widget.attrs["placeholder"] = "Email address"

    class Meta:
        model = Property
        fields = [
            'title',  # Property title/name
            'description',  # Detailed description
            'price',  # Rental/selling price
            'location',  # Property location
            'contact_name',  # Owner's contact name
            'contact_phone',  # Owner's phone number
            'contact_email',  # Owner's email
            'property_type',  # Rent or Sell
            'image',  # Main property image
            'latitude',  # GPS latitude for map
            'longitude',  # GPS longitude for map
        ]

    def clean_location(self):
        location = (self.cleaned_data.get("location") or "").strip()
        if self.COORDINATE_LOCATION_RE.match(location):
            raise ValidationError("Please enter a location name (not latitude/longitude).")
        return location


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating user account information.
    Allows users to edit name, email, and username.
    """
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information.
    Allows users to add phone number and profile picture.
    """
    class Meta:
        model = Profile
        fields = ["phone_number", "image"]
        widgets = {
            "image": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to all fields
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs["class"] = "form-control"
            else:
                field.widget.attrs["class"] = "form-control"
            # Add placeholder for phone number field
            if name == "phone_number":
                field.widget.attrs["placeholder"] = "Phone number"


class TestimonialForm(forms.ModelForm):
    """
    Form for users to submit testimonials and reviews.
    Collects user role, rating, and written feedback.
    """
    class Meta:
        model = Testimonial
        fields = ["role", "rating", "message"]
        widgets = {
            "rating": forms.Select(),  # Dropdown for rating selection
            "message": forms.Textarea(  # Textarea for longer feedback
                attrs={
                    "rows": 4,
                    "placeholder": "Share your experience with our platform...",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to all fields
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
