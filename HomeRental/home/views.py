from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from .models import (
    home,
    Property,
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
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_user_model
from django.http import HttpResponseForbidden

User = get_user_model()

def about(request):
    """Display the about page with company info, stats, team, and FAQs"""
    stats = [
        {'number': '5,000+', 'label': 'Properties Listed'},
        {'number': '10,000+', 'label': 'Happy Tenants'},
        {'number': '2,500+', 'label': 'Active Landlords'},
        {'number': '15,000+', 'label': 'Successful Bookings'},
    ]
    
    team_members = [
        {
            'name': 'Rajesh Kumar',
            'role': 'Founder & CEO',
            'bio': 'Visionary leader with 15+ years in real estate technology',
            'icon': 'fa-user-tie'
        },
        {
            'name': 'Priya Sharma',
            'role': 'CTO',
            'bio': 'Tech expert specializing in scalable web platforms',
            'icon': 'fa-computer'
        },
        {
            'name': 'Amit Patel',
            'role': 'Head of Operations',
            'bio': 'Operations specialist ensuring smooth user experiences',
            'icon': 'fa-cogs'
        },
        {
            'name': 'Neha Singh',
            'role': 'Customer Success Manager',
            'bio': 'Dedicated to providing exceptional customer service',
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
            'answer': 'Once you book a property, you can message the landlord directly through our platform. They typically respond within a few hours.'
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
            'title': 'Direct Messaging',
            'description': 'Communicate directly with landlords and tenants',
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
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        testimonial_form = TestimonialForm(request.POST)
        if testimonial_form.is_valid():
            testimonial = testimonial_form.save(commit=False)
            testimonial.user = request.user
            testimonial.save()
            return redirect("home_list")
    else:
        testimonial_form = TestimonialForm()

    testimonials = Testimonial.objects.select_related("user").order_by("-created_at")[:6]
    return render(
        request,
        "index.html",
        {
            "testimonials": testimonials,
            "testimonial_form": testimonial_form,
        },
    )


def home_list(request):
    homes = home.objects.all().order_by('-created_at')
    return render(request, 'home_list.html', {'homes': homes})

@login_required
def home_create(request):
    if request.method == "POST":
        form = homeForm(request.POST, request.FILES)
        if form.is_valid():
            home_obj = form.save(commit=False)
            home_obj.user = request.user
            home_obj.save()
            return redirect('home_list')
    else:
        form = homeForm()
    return render(request, 'home_form.html', {'form': form})

@login_required
def home_edit(request, home_id):
    home_obj = get_object_or_404(home, pk=home_id, user=request.user)
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
    home_obj = get_object_or_404(home, pk=home_id, user=request.user)
    if request.method == 'POST':
        home_obj.delete()
        return redirect('home_list')
    return render(request, 'home_confirm_delete.html', {'home': home_obj})

# for the  login gistration
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form':form})


# For the property.html
@login_required
def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.user = request.user
            prop.save()
            return redirect('properties')
    else:
        form = PropertyForm()

    return render(request, 'add_property.html', {'form': form})


def property_list(request):
    sort_option = request.GET.get("sort", "")
    selected_location = request.GET.get("location", "")

    properties = Property.objects.all()

    if selected_location:
        properties = properties.filter(location__iexact=selected_location)

    if sort_option == "low_to_high":
        properties = properties.order_by("price")
    elif sort_option == "high_to_low":
        properties = properties.order_by("-price")

    locations = (
        Property.objects.exclude(location__isnull=True)
        .exclude(location__exact="")
        .order_by("location")
        .values_list("location", flat=True)
        .distinct()
    )

    context = {
        "properties": properties,
        "locations": locations,
        "selected_location": selected_location,
        "sort_option": sort_option,
    }

    return render(request, "property_list.html", context)

def property_detail(request, property_id):
    property_obj = get_object_or_404(Property, pk=property_id)
    is_compact_view = request.GET.get('view') == 'compact'
    booked_tenants = []

    if request.user.is_authenticated and request.user == property_obj.user:
        property_bookings = Booking.objects.filter(
            property=property_obj,
            owner=request.user,
        ).select_related('booked_by').order_by('-booked_at')

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
    })


@login_required
def property_edit(request, property_id):
    prop = get_object_or_404(Property, pk=property_id, user=request.user)
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.user = request.user
            prop.save()
            return redirect('properties')
    else:
        form = PropertyForm(instance=prop)
    return render(request, 'add_property.html', {'form': form})


@login_required
def property_delete(request, property_id):
    prop = get_object_or_404(Property, pk=property_id, user=request.user)
    if request.method == 'POST':
        prop.delete()
        return redirect('properties')
    return render(request, 'property_confirm_delete.html', {'property': prop})


@login_required
def book_property(request, property_id):
    property = get_object_or_404(Property, id=property_id)

    if request.method == "POST" and request.user != property.user:
        Booking.objects.get_or_create(
            property=property,
            booked_by=request.user,
            owner=property.user,
        )

    return redirect('properties')

@login_required
def notifications(request):
    owner_notifications_qs = request.user.owner_bookings.select_related(
        "booked_by", "property"
    )
    tenant_notifications_qs = request.user.cancellation_notifications.select_related(
        "owner", "property"
    )
    tenant_acceptance_qs = request.user.acceptance_notifications.select_related(
        "owner", "property"
    )

    if request.method == "GET":
        owner_notifications_qs.filter(is_read=False).update(is_read=True)
        tenant_notifications_qs.filter(is_read=False).update(is_read=True)
        tenant_acceptance_qs.filter(is_read=False).update(is_read=True)

    notifications = []
    for item in owner_notifications_qs:
        notifications.append(
            {
                "message": f"{item.booked_by.username} booked your property {item.property.title}",
                "created_at": item.booked_at,
                "is_read": item.is_read,
                "can_cancel": item.is_read,
                "can_accept": item.is_read and not item.is_accepted,
                "is_accepted": item.is_accepted,
                "booking_id": item.id,
            }
        )

    for item in tenant_notifications_qs:
        notifications.append(
            {
                "message": f"{item.owner.username} canceled your booking for {item.property.title}",
                "created_at": item.canceled_at,
                "is_read": item.is_read,
                "can_cancel": False,
                "can_accept": False,
                "is_accepted": False,
                "booking_id": None,
            }
        )

    for item in tenant_acceptance_qs:
        notifications.append(
            {
                "message": f"{item.owner.username} accepted your booking for {item.property.title}",
                "created_at": item.accepted_at,
                "is_read": item.is_read,
                "can_cancel": False,
                "can_accept": False,
                "is_accepted": False,
                "booking_id": None,
            }
        )

    notifications.sort(key=lambda n: n["created_at"], reverse=True)

    return render(request, 'notifications.html', {
        'notifications': notifications
    })


@login_required
def cancel_booking(request, booking_id):
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', 'properties'))

    booking = Booking.objects.filter(
        pk=booking_id,
        owner=request.user,
        is_read=True,
    ).first()

    if not booking:
        return redirect(request.META.get('HTTP_REFERER', 'properties'))

    BookingCancellationNotification.objects.create(
        property=booking.property,
        tenant=booking.booked_by,
        owner=booking.owner,
    )
    booking.delete()
    return redirect(request.META.get('HTTP_REFERER', 'properties'))


@login_required
def accept_booking(request, booking_id):
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', 'notifications'))

    booking = Booking.objects.filter(
        pk=booking_id,
        owner=request.user,
        is_read=True,
    ).first()

    if not booking or booking.is_accepted:
        return redirect(request.META.get('HTTP_REFERER', 'notifications'))

    BookingAcceptanceNotification.objects.create(
        property=booking.property,
        tenant=booking.booked_by,
        owner=booking.owner,
    )
    booking.is_accepted = True
    booking.save(update_fields=["is_accepted"])
    return redirect(request.META.get('HTTP_REFERER', 'notifications'))


@login_required
def tenant_profile(request, user_id):
    tenant = get_object_or_404(User, pk=user_id)

    can_view = Booking.objects.filter(
        owner=request.user,
        booked_by=tenant,
    ).exists()

    if not can_view:
        return HttpResponseForbidden("You are not allowed to view this profile.")

    tenant_profile_obj = Profile.objects.filter(user=tenant).first()
    tenant_bookings = Booking.objects.filter(
        owner=request.user,
        booked_by=tenant,
    ).select_related('property').order_by('-booked_at')

    return render(
        request,
        'tenant_profile.html',
        {
            'tenant': tenant,
            'tenant_profile': tenant_profile_obj,
            'tenant_bookings': tenant_bookings,
        },
    )


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Booking, pk=notification_id, owner=request.user
    )

    if request.method == 'POST':
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    return redirect('notifications')


@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Booking.objects.filter(owner=request.user, is_read=False).update(is_read=True)
        BookingCancellationNotification.objects.filter(
            tenant=request.user,
            is_read=False,
        ).update(is_read=True)
        BookingAcceptanceNotification.objects.filter(
            tenant=request.user,
            is_read=False,
        ).update(is_read=True)

    return redirect(request.META.get('HTTP_REFERER', 'notifications'))


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=profile_obj
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile_obj)

    return render(
        request,
        "profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )
