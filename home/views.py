"""
Views Module - Home Rental System
Handles all request-response logic for the application.
Contains views for property management, bookings, notifications, user profiles, and authentication.
"""

from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from .models import (
    home,
    Property,
    Favorite,
    Booking,
    Profile,
    BookingCancellationNotification,
    BookingAcceptanceNotification,
    Testimonial,
)
from .forms import (
    PropertyForm,
    homeForm,
    UserRegistrationForm,
    UserUpdateForm,
    ProfileUpdateForm,
    TestimonialForm,
)
from .email_notifications import (
    send_booking_accepted_email,
    send_booking_canceled_email,
    send_booking_confirmation_email,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_user_model
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponseForbidden
from django.utils import timezone
import re
from urllib.parse import urlencode

User = get_user_model()  # Get the User model for use throughout views
COORDINATE_LOCATION_RE = re.compile(r"^\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*$")
ACCEPTED_CHAT_NOTIFICATION_MESSAGE = "Your booking has been accepted. You can now chat with the owner."

def about(request):
    """
    Display the about page with company information, statistics, team members, and features.
    Shows company overview, team details, FAQs, and service features.
    """
    stats = [
        {'number': '5,000+', 'label': 'Properties Listed'},
        {'number': '10,000+', 'label': 'Happy Tenants'},
        {'number': '2,500+', 'label': 'Active Landlords'},
        {'number': '15,000+', 'label': 'Successful Bookings'},
    ]
    
    team_members = [
        {
            'name': 'Aashish Kumar Shah',
            'role': 'Leader',
            'bio': 'Student of Bsc.(HONS) Computing',
            'icon': ''
        },
        {
            'name': 'Abhishek Koirala',
            'role': 'Member',
            'bio': 'Student of Bsc.(HONS) Computing',
            'icon': 'fa-computer'
        },
        {
            'name': 'Anushka Sangroula',
            'role': 'Member',
            'bio': 'Student of Bsc.(HONS) Computing',
            'icon': 'fa-cogs'
        },
        {
            'name': 'Hirdaya Shiwakoti',
            'role': 'Member',
            'bio': 'Student of Bsc.(HONS) Computing',
            'icon': 'fa-headset'
        },
    ]
    
    faqs = [
        {
            'question': 'How do I list my property?',
            'answer': 'Simply sign up, create an account, and click "List Your Property". Fill in the details, upload photos, and publish your listing. Your property will be visible to thousands of tenants.'
        },
        {
            'question': 'Is it safe to book a property?',
            'answer': 'Yes! All properties are verified by our team. We also provide secure payment processing and 24/7 customer support to ensure safe transactions.'
        },
        {
            'question': 'What are the fees involved?',
            'answer': 'We charge a small listing fee for property owners and a booking fee for tenants. There are no hidden charges - all fees are clearly mentioned upfront.'
        },
        {
            'question': 'How do I contact the landlord?',
            'answer': 'Once your booking is accepted, you can use the owner contact details shared in your booking update to reach them directly.'
        },
        {
            'question': 'Can I cancel a booking?',
            'answer': 'Yes, you can cancel within 24 hours of booking for a full refund. After that, cancellation policies vary by property.'
        },
        {
            'question': 'How are disputes resolved?',
            'answer': 'Our support team mediates disputes between landlords and tenants. We aim to resolve all issues fairly and quickly.'
        },
    ]
    
    features = [
        {
            'title': 'Easy Property Listing',
            'description': 'List your property in minutes with our simple interface',
            'icon': 'fa-home'
        },
        {
            'title': 'Verified Listings',
            'description': 'All properties are verified for authenticity and safety',
            'icon': 'fa-check-circle'
        },
        {
            'title': 'Secure Payments',
            'description': 'Safe and encrypted payment processing',
            'icon': 'fa-credit-card'
        },
        {
            'title': '24/7 Support',
            'description': 'Round-the-clock customer support for all your needs',
            'icon': 'fa-life-ring'
        },
        {
            'title': 'Easy Contact',
            'description': 'Reach landlords and tenants using the contact details shared on listings and updates',
            'icon': 'fa-envelope'
        },
        {
            'title': 'Mobile Friendly',
            'description': 'Access your account anytime, anywhere',
            'icon': 'fa-mobile-alt'
        },
    ]
    
    return render(request, 'about.html', {
        'stats': stats,
        'team_members': team_members,
        'faqs': faqs,
        'features': features,
    })


def index(request):
    """
    Display homepage with latest testimonials.
    Shows 6 most recent testimonials from users to showcase platform credibility.
    """
    testimonials = Testimonial.objects.select_related("user").order_by("-created_at")[:6]
    return render(
        request,
        "index.html",
        {
            "testimonials": testimonials,
        },
    )


def reviews(request):
    """
    Display reviews page and handle new testimonial submissions.
    
    GET: Show all testimonials and empty form for new submission
    POST: Save new testimonial if user is authenticated
    """
    if request.method == "POST":
        # Check if user is logged in before accepting testimonial
        if not request.user.is_authenticated:
            return redirect("login")
        testimonial_form = TestimonialForm(request.POST)
        if testimonial_form.is_valid():
            # Save testimonial with current user
            testimonial = testimonial_form.save(commit=False)
            testimonial.user = request.user
            testimonial.save()
            return redirect("reviews")
    else:
        testimonial_form = TestimonialForm()

    # Display all testimonials sorted by most recent
    testimonials = Testimonial.objects.select_related("user").order_by("-created_at")
    return render(
        request,
        "reviews.html",
        {
            "testimonials": testimonials,
            "testimonial_form": testimonial_form,
        },
    )


def help_page(request):
    """
    Display help page with FAQ section and contact form.
    
    GET: Show FAQ and contact form
    POST: Validate and process contact form submission
    """
    # FAQ items with keywords for search functionality
    faq_items = [
                {
            "question": "How do I create an account?",
            "answer": "Go to Register from the navbar, fill in your details, and submit the form to create your account.",
            "keywords": "account register sign up login",
        },
        {
            "question": "How do I list a property?",
            "answer": "Login first, open the property form, enter property details, choose the map location, upload an image, and submit.",
            "keywords": "list property owner upload",
        },
        {
            "question": "How can I book a property?",
            "answer": "Open a property from the listings page and click Book Now. Your booking request is sent to the property owner.",
            "keywords": "book booking tenant reserve",
        },
        {
            "question": "How will I know if my booking is accepted?",
            "answer": "You will receive a notification in the system when the owner accepts your booking.",
            "keywords": "booking accepted notification update",
        },
        {
            "question": "How do I contact the property owner?",
            "answer": "Open the property details page and use the provided contact information to reach the owner.",
            "keywords": "contact owner landlord phone email",
        },
    ]

    # Pre-fill form with logged-in user's data if available
    form_data = {
        "name": request.user.get_full_name() if request.user.is_authenticated else "",
        "email": request.user.email if request.user.is_authenticated else "",
        "subject": "",
        "message": "",
        "preferred_contact": "email",
    }

    # Handle contact form submission
    if request.method == "POST":
        # Collect form data from POST request
        form_data = {
            "name": request.POST.get("name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "subject": request.POST.get("subject", "").strip(),
            "message": request.POST.get("message", "").strip(),
            "preferred_contact": request.POST.get("preferred_contact", "email").strip() or "email",
        }

        # Validate all required fields are filled
        required_values = [form_data["name"], form_data["email"], form_data["subject"], form_data["message"]]
        if not all(required_values):
            messages.error(request, "Please complete all required fields before sending your message.")
        # Validate message has minimum length
        elif len(form_data["message"]) < 20:
            messages.error(request, "Please write at least 20 characters in your message for better support.")
        else:
            try:
                validate_email(form_data["email"])
            except ValidationError:
                messages.error(request, "Please enter a valid email address.")
            else:
                messages.success(
                    request,
                    "Thanks! Your message has been received. Our support team will contact you shortly.",
                )
                return redirect("help")

    return render(
        request,
        "help.html",
        {
            "faq_items": faq_items,
            "form_data": form_data,
        },
    )


def home_list(request):
    """
    Display all home entries ordered by most recent.
    Legacy functionality for storing general home-related content.
    """
    homes = home.objects.all().order_by('-created_at')
    return render(request, 'home_list.html', {'homes': homes})

@login_required  # User must be logged in to create
def home_create(request):
    """
    Create a new home entry with text and photo.
    Only accessible to authenticated users.
    
    GET: Display empty form
    POST: Save new home entry with authenticated user as creator
    """
    if request.method == "POST":
        form = homeForm(request.POST, request.FILES)
        if form.is_valid():
            home_obj = form.save(commit=False)
            home_obj.user = request.user  # Associate with current user
            home_obj.save()
            return redirect('home_list')
    else:
        form = homeForm()
    return render(request, 'home_form.html', {'form': form})

@login_required
def home_edit(request, home_id):
    """
    Edit an existing home entry.
    Only the owner of the entry can edit it.
    
    GET: Display pre-filled form
    POST: Update home entry in database
    """
    home_obj = get_object_or_404(home, pk=home_id, user=request.user)  # Verify ownership
    if request.method == 'POST':
        form = homeForm(request.POST, request.FILES, instance=home_obj)
        if form.is_valid():
            home_obj = form.save(commit=False)
            home_obj.user = request.user
            home_obj.save()
            return redirect('home_list')
    else:
        form = homeForm(instance=home_obj)
    return render(request, 'home_form.html', {'form': form})

@login_required
def home_delete(request, home_id):
    """
    Delete a home entry after confirmation.
    Only the owner can delete their own entries.
    
    GET: Display confirmation page
    POST: Delete entry from database
    """
    home_obj = get_object_or_404(home, pk=home_id, user=request.user)  # Verify ownership
    if request.method == 'POST':
        home_obj.delete()
        return redirect('home_list')
    return render(request, 'home_confirm_delete.html', {'home': home_obj})


def register(request):
    """
    User registration page.
    Handles user account creation with validation.
    
    GET: Display registration form
    POST: Create new user if form is valid, then auto-login and redirect
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Create new user
            login(request, user)  # Auto-login after registration
            return redirect('home_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def add_property(request):
    """
    Add a new property listing.
    Only accessible to authenticated users (property owners).
    
    GET: Display empty property form
    POST: Create new property listing with current user as owner
    """
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.user = request.user  # Set property owner
            prop.save()
            return redirect('my_properties')
    else:
        form = PropertyForm()

    return render(request, 'add_property.html', {'form': form})


def _build_property_list_context(request, base_queryset, *, scope="all"):
    """
    Build context for property listing pages.

    Parameters:
    - base_queryset: Base Property queryset before applying UI filters
    - scope: "all" | "mine" | "others" (used for UI labels and nav state)
    """
    sort_option = request.GET.get("sort", "")  # Get sort parameter from URL
    selected_location = request.GET.get("location", "")  # Get location filter from URL
    if selected_location and COORDINATE_LOCATION_RE.match(selected_location):
        selected_location = ""

    # Apply filters to the base queryset
    properties = base_queryset
    if selected_location:
        properties = properties.filter(location__iexact=selected_location)

    # Apply price sorting
    if sort_option == "low_to_high":
        properties = properties.order_by("price")
    elif sort_option == "high_to_low":
        properties = properties.order_by("-price")

    # Get all unique locations for filter dropdown (based on the current scope)
    locations_qs = (
        base_queryset.exclude(location__isnull=True)
        .exclude(location__exact="")
        .order_by("location")
        .values_list("location", flat=True)
        .distinct()
    )
    locations = [loc for loc in locations_qs if loc and not COORDINATE_LOCATION_RE.match(loc)]

    page_title = "Browse Properties"
    page_subtitle = "Find your perfect rental home"
    if scope == "mine":
        page_title = "My Properties"
        page_subtitle = "Manage your property listings"
    elif scope == "others":
        page_title = "Browse Properties"
        page_subtitle = "Browse listings from other owners"

    filter_params = {}
    if selected_location:
        filter_params["location"] = selected_location
    if sort_option:
        filter_params["sort"] = sort_option
    filter_query = f"?{urlencode(filter_params)}" if filter_params else ""

    context = {
        "properties": properties,
        "locations": locations,
        "selected_location": selected_location,
        "sort_option": sort_option,
        "filter_query": filter_query,
        "favorite_property_ids": set(),
        "scope": scope,
        "page_title": page_title,
        "page_subtitle": page_subtitle,
    }

    # If user is logged in, get their favorite properties
    if request.user.is_authenticated:
        context["favorite_property_ids"] = set(
            Favorite.objects.filter(user=request.user).values_list("property_id", flat=True)
        )

    return context


def property_list(request):
    """
    Display properties with filtering and sorting options.
    
    Supports:
    - Location filtering: Filter by property location
    - Price sorting: Sort by price (low to high or high to low)
    - Favorites tracking: Shows which properties user has favorited
    """
    qs = Property.objects.all()
    if request.user.is_authenticated:
        # Default to browsing other users' properties (Facebook-like explore behavior)
        qs = qs.exclude(user=request.user)
    context = _build_property_list_context(request, qs, scope="others")
    return render(request, "property_list.html", context)


@login_required
def my_properties(request):
    """
    Display properties created by the currently logged-in user.
    Useful for owners to manage their own listings.
    """
    context = _build_property_list_context(
        request, Property.objects.filter(user=request.user), scope="mine"
    )
    return render(request, "property_list.html", context)


def other_properties(request):
    """
    Display properties that are not owned by the currently logged-in user.
    For anonymous users, this behaves like the main properties list.
    """
    qs = Property.objects.all()
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)
    context = _build_property_list_context(request, qs, scope="others")
    return render(request, "property_list.html", context)

def property_detail(request, property_id):
    """
    Display detailed information about a specific property.
    Shows all property details, contact info, map, and booked tenants (if owner).
    
    For property owners, displays list of users who have booked this property.
    """
    property_obj = get_object_or_404(Property, pk=property_id)  # Get property or 404
    is_compact_view = request.GET.get('view') == 'compact'  # Check for compact view mode
    booked_tenants = []

    # If current user is the property owner, show list of tenants who booked
    if request.user.is_authenticated and request.user == property_obj.user:
        # Get all bookings for this property
        property_bookings = Booking.objects.filter(
            property=property_obj,
            owner=request.user,
        ).exclude(
            status=Booking.Status.REJECTED,
        ).select_related('booked_by').order_by('-booked_at')

        # Build list of unique tenants (avoid duplicates if user booked multiple times)
        seen_user_ids = set()
        for booking in property_bookings:
            if booking.booked_by_id not in seen_user_ids:
                seen_user_ids.add(booking.booked_by_id)
                booked_tenants.append(
                    {
                        "id": booking.booked_by_id,
                        "username": booking.booked_by.username,
                    }
                )

    return render(request, 'property_detail.html', {
        'property': property_obj,
        'is_compact_view': is_compact_view,
        'booked_tenants': booked_tenants,
        'is_favorited': (
            # Check if current user has this property in favorites
            request.user.is_authenticated
            and Favorite.objects.filter(user=request.user, property=property_obj).exists()
        ),
    })


@login_required
def property_edit(request, property_id):
    """
    Edit an existing property listing.
    Only the property owner can edit their listing.
    
    GET: Display pre-filled property form
    POST: Update property in database
    """
    prop = get_object_or_404(Property, pk=property_id, user=request.user)  # Verify ownership
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.user = request.user
            prop.save()
            return redirect('my_properties')
    else:
        form = PropertyForm(instance=prop)
    return render(request, 'add_property.html', {'form': form})


@login_required
def property_delete(request, property_id):
    """
    Delete a property listing.
    Only the property owner can delete their listing.
    
    GET: Display confirmation page
    POST: Delete property from database
    """
    prop = get_object_or_404(Property, pk=property_id, user=request.user)  # Verify ownership
    if request.method == 'POST':
        prop.delete()
        return redirect('my_properties')
    return render(request, 'property_confirm_delete.html', {'property': prop})


@login_required
def toggle_favorite(request, property_id):
    """
    Add or remove a property from user's favorites (bookmarks).
    
    POST only: Toggles favorite status - adds if not favorited, removes if already favorited
    Redirects back to previous page after action
    """
    if request.method != "POST":
        return redirect(request.META.get("HTTP_REFERER", "properties"))

    property_obj = get_object_or_404(Property, pk=property_id)
    favorite = Favorite.objects.filter(user=request.user, property=property_obj).first()

    # Remove favorite if exists, otherwise create new
    if favorite:
        favorite.delete()  # Un-favorite
    else:
        Favorite.objects.create(user=request.user, property=property_obj)  # Add to favorites

    return redirect(request.META.get("HTTP_REFERER", "properties"))


@login_required
def favorite_list(request):
    """
    Display user's list of favorited (saved) properties.
    Shows all properties the user has bookmarked, sorted by most recent.
    """
    favorites = (
        Favorite.objects.filter(user=request.user)
        .select_related("property")
        .order_by("-created_at")  # Most recently favorited first
    )
    return render(request, "favorite_list.html", {"favorites": favorites})


@login_required
def book_property(request, property_id):
    """
    Create a booking request for a property.
    
    POST only: Creates or updates a booking request from tenant to property owner
    Prevents users from booking their own properties
    """
    property = get_object_or_404(Property, id=property_id)

    # Only allow booking if user is not the property owner
    if request.method == "POST" and request.user != property.user:
        # Try to get existing booking, create if doesn't exist
        booking, created = Booking.objects.get_or_create(
            property=property,
            booked_by=request.user,
            owner=property.user,
        )
        if booking.status == Booking.Status.ACCEPTED:
            messages.info(
                request,
                "This booking is already accepted. You can open the chat from your notifications page.",
            )
            return redirect("notifications")

        # If booking already existed, reset it to a fresh pending request
        if not created:
            booking.is_read = False
            booking.booked_at = timezone.now()  # Update booking timestamp

        booking.mark_pending()
        booking.save(update_fields=["status", "is_accepted", "is_read", "booked_at"])

        # Email customer a confirmation (won't block booking creation if it fails)
        send_booking_confirmation_email(request, booking)

    return redirect('properties')

@login_required
def notifications(request):
    """
    Display all notifications for the current user.
    
    Handles three types of notifications:
    1. Booking requests (for property owners)
    2. Booking cancellations (for tenants)
    3. Booking acceptances (for tenants)
    
    GET: Mark all unread notifications as read and display them
    """
    # Fetch owner bookings (booking requests from tenants)
    owner_notifications_qs = request.user.owner_bookings.select_related(
        "booked_by", "property"
    ).exclude(status=Booking.Status.REJECTED)
    # Fetch cancellation notifications for current user
    tenant_notifications_qs = request.user.cancellation_notifications.select_related(
        "owner", "property"
    )
    # Fetch acceptance notifications for current user
    tenant_acceptance_qs = request.user.acceptance_notifications.select_related(
        "owner", "owner__profile", "property", "booking"
    )

    # Mark all unread notifications as read on GET request
    if request.method == "GET":
        owner_notifications_qs.filter(is_read=False).update(is_read=True)
        tenant_notifications_qs.filter(is_read=False).update(is_read=True)
        tenant_acceptance_qs.filter(is_read=False).update(is_read=True)

    # ===== BUILD OWNER NOTIFICATIONS =====
    # Bookings on properties owned by user
    notifications = []
    for item in owner_notifications_qs:
        notifications.append(
            {
                "kind": "booking_request",
                "type_label": "Booking request",
                "accent": "primary",
                "icon": "fa-calendar-plus",
                "message": f"{item.booked_by.username} booked your property {item.property.title}",
                "created_at": item.booked_at,
                "is_read": item.is_read,
                "can_cancel": item.is_read,  # Can cancel after owner has seen notification
                "can_accept": item.is_read and item.status == Booking.Status.PENDING,
                "can_chat": item.chat_enabled,
                "chat_label": "Chat Now",
                "is_accepted": item.status == Booking.Status.ACCEPTED,
                "booking_id": item.id,
                "property_id": item.property.id,
            }
        )

    # ===== BUILD TENANT CANCELLATION NOTIFICATIONS =====
    # When owner cancels tenant's booking
    for item in tenant_notifications_qs:
        notifications.append(
            {
                "kind": "booking_canceled",
                "type_label": "Canceled",
                "accent": "danger",
                "icon": "fa-circle-xmark",
                "message": f"{item.owner.username} canceled your booking for {item.property.title}",
                "created_at": item.canceled_at,
                "is_read": item.is_read,
                "can_cancel": False,
                "can_accept": False,
                "can_chat": False,
                "is_accepted": False,
                "booking_id": None,
                "property_id": item.property.id,
            }
        )

    # ===== BUILD TENANT ACCEPTANCE NOTIFICATIONS =====
    # When owner accepts tenant's booking
    for item in tenant_acceptance_qs:
        chat_booking = item.booking if item.booking and item.booking.chat_enabled else None
        if not chat_booking:
            chat_booking = Booking.objects.filter(
                property=item.property,
                booked_by=item.tenant,
                owner=item.owner,
                status=Booking.Status.ACCEPTED,
            ).first()
        booking_id = chat_booking.id if chat_booking else None

        notifications.append(
            {
                "kind": "booking_accepted",
                "type_label": "Accepted",
                "accent": "success",
                "icon": "fa-circle-check",
                "message": ACCEPTED_CHAT_NOTIFICATION_MESSAGE,
                "created_at": item.accepted_at,
                "is_read": item.is_read,
                "can_cancel": False,
                "can_accept": False,
                "can_chat": bool(chat_booking),
                "chat_label": "Chat Now",
                "is_accepted": True,
                "booking_id": booking_id,
                "property_id": item.property.id,
            }
        )

    # Sort all notifications by date (newest first)
    notifications.sort(key=lambda n: n["created_at"], reverse=True)

    return render(request, 'notifications.html', {
        'notifications': notifications
    })


@login_required
def cancel_booking(request, booking_id):
    """
    Cancel a booking request (owner only).
    
    POST only: Owner can cancel a booking and send cancellation notification to tenant
    Creates a BookingCancellationNotification record so tenant is notified
    """
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', 'properties'))

    # Only property owner can cancel - verify with is_read check
    booking = Booking.objects.filter(
        pk=booking_id,
        owner=request.user,
        is_read=True,
    ).exclude(status=Booking.Status.REJECTED).first()

    if not booking:
        return redirect(request.META.get('HTTP_REFERER', 'properties'))

    # Create notification for tenant about cancellation
    BookingCancellationNotification.objects.create(
        property=booking.property,
        tenant=booking.booked_by,
        owner=booking.owner,
    )

    cancellation_reason = (
        "The property owner canceled your accepted booking."
        if booking.is_accepted
        else "The property owner rejected your booking request."
    )
    refund_details = (
        "No payment is collected through Ghar Setu, so refunds are not processed here. "
        "If you made a payment directly to the owner, please contact them for next steps."
    )

    # Email tenant about cancellation (best-effort)
    send_booking_canceled_email(
        request,
        booking,
        cancellation_reason=cancellation_reason,
        refund_details=refund_details,
    )
    booking.mark_rejected()
    booking.save(update_fields=["status", "is_accepted"])
    return redirect(request.META.get('HTTP_REFERER', 'properties'))


@login_required
def accept_booking(request, booking_id):
    """
    Accept a booking request (owner only).
    
    POST only: Owner can accept a booking request
    Creates a BookingAcceptanceNotification so tenant is notified
    Sets booking.is_accepted to True to prevent further changes
    """
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', 'notifications'))

    # Only property owner can accept - verify with is_read check
    booking = Booking.objects.filter(
        pk=booking_id,
        owner=request.user,
        is_read=True,
        status=Booking.Status.PENDING,
    ).first()

    # Don't allow accepting if already accepted or booking doesn't exist
    if not booking:
        return redirect(request.META.get('HTTP_REFERER', 'notifications'))

    # Create acceptance notification for tenant
    BookingAcceptanceNotification.objects.create(
        property=booking.property,
        booking=booking,
        tenant=booking.booked_by,
        owner=booking.owner,
    )
    # Mark booking as accepted
    booking.mark_accepted()
    booking.save(update_fields=["status", "is_accepted"])

    # Email tenant with acceptance confirmation (best-effort)
    send_booking_accepted_email(request, booking)
    return redirect(request.META.get('HTTP_REFERER', 'notifications'))


@login_required
def tenant_profile(request, user_id):
    """
    View a tenant's profile (owner only).
    Shows tenant information and their bookings on owner's properties.
    
    Security: Only shows profile if current user has had bookings with this tenant
    """
    tenant = get_object_or_404(User, pk=user_id)

    # Security check: only allow viewing if owner has booked with this tenant
    can_view = Booking.objects.filter(
        owner=request.user,
        booked_by=tenant,
    ).exists()

    if not can_view:
        return HttpResponseForbidden("You are not allowed to view this profile.")

    # Get tenant's profile info if exists
    tenant_profile_obj = Profile.objects.filter(user=tenant).first()

    # Get all bookings this tenant made on owner's properties
    tenant_bookings = Booking.objects.filter(
        owner=request.user,
        booked_by=tenant,
    ).select_related('property').order_by('-booked_at')

    tenant_bookings_count = tenant_bookings.count()
    accepted_bookings_count = tenant_bookings.filter(status=Booking.Status.ACCEPTED).count()
    distinct_properties_count = (
        tenant_bookings.values_list("property_id", flat=True).distinct().count()
    )
    latest_booking = tenant_bookings.first()

    return render(
        request,
        'tenant_profile.html',
        {
            'tenant': tenant,
            'tenant_profile': tenant_profile_obj,
            'tenant_bookings': tenant_bookings,
            'tenant_bookings_count': tenant_bookings_count,
            'accepted_bookings_count': accepted_bookings_count,
            'distinct_properties_count': distinct_properties_count,
            'latest_booking_date': getattr(latest_booking, "booked_at", None),
        },
    )


@login_required
def mark_notification_read(request, notification_id):
    """
    Mark a single notification as read.
    
    POST only: Sets is_read flag on notification to True
    Used when user clicks on a notification to read it
    """
    notification = get_object_or_404(
        Booking, pk=notification_id, owner=request.user
    )

    if request.method == 'POST':
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    return redirect('notifications')


@login_required
def mark_all_notifications_read(request):
    """
    Mark all notifications for current user as read.
    
    POST only: Updates is_read flag across all notification types
    Useful for "Mark all as read" button in notification panel
    """
    if request.method == 'POST':
        # Mark all booking notifications as read
        Booking.objects.filter(owner=request.user, is_read=False).update(is_read=True)
        # Mark all cancellation notifications as read
        BookingCancellationNotification.objects.filter(
            tenant=request.user,
            is_read=False,
        ).update(is_read=True)
        # Mark all acceptance notifications as read
        BookingAcceptanceNotification.objects.filter(
            tenant=request.user,
            is_read=False,
        ).update(is_read=True)

    return redirect(request.META.get('HTTP_REFERER', 'notifications'))


@login_required
def profile(request):
    """
    Display and edit user profile.
    Shows user account info and profile information with photo.
    
    GET: Display current profile information
    POST: Update user and profile information
    """
    # Get or create user profile
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    # ===== PROFILE STATS / ACTIVITY (for a richer profile page) =====
    my_properties_qs = Property.objects.filter(user=request.user).order_by("-created_at")
    favorites_qs = (
        Favorite.objects.filter(user=request.user)
        .select_related("property")
        .order_by("-created_at")
    )
    bookings_as_tenant_qs = (
        Booking.objects.filter(booked_by=request.user)
        .select_related("property", "owner")
        .order_by("-booked_at")
    )
    booking_requests_qs = (
        Booking.objects.filter(owner=request.user)
        .exclude(status=Booking.Status.REJECTED)
        .select_related("property", "booked_by")
        .order_by("-booked_at")
    )

    completion_total = 5
    completion_filled = sum(
        [
            bool(request.user.first_name),
            bool(request.user.last_name),
            bool(request.user.email),
            bool(profile_obj.phone_number),
            bool(profile_obj.image),
        ]
    )
    profile_completion = int((completion_filled / completion_total) * 100)

    active_tab = request.GET.get("tab") or (
        "settings" if request.method == "POST" else "overview"
    )

    if request.method == "POST":
        # Process both user form and profile form
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=profile_obj
        )
        # Save both forms if valid
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")

        # If forms are invalid, keep Settings tab open so errors are visible
        active_tab = "settings"
    else:
        # Load existing data into forms
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile_obj)

    return render(
        request,
        "profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "active_tab": active_tab,
            "profile_completion": profile_completion,
            "my_properties_count": my_properties_qs.count(),
            "favorites_count": favorites_qs.count(),
            "bookings_as_tenant_count": bookings_as_tenant_qs.count(),
            "booking_requests_count": booking_requests_qs.count(),
            "my_properties": my_properties_qs[:6],
            "recent_favorites": favorites_qs[:6],
            "recent_bookings_as_tenant": bookings_as_tenant_qs[:6],
            "recent_booking_requests": booking_requests_qs[:6],
        },
    )
