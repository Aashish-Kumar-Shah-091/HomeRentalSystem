from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home_list'),
    path('about/', views.about, name='about'),
    path('home/', views.index, name='home'),
    path('homes/', views.home_list, name='homes'),
    path('create/', views.home_create, name='home_create'),
    path('<int:home_id>/edit/', views.home_edit, name='home_edit'),
    path('<int:home_id>/delete/', views.home_delete, name='home_delete'),
    path('register/', views.register, name='register'),
    path('property/', views.add_property, name='property'),
    path('properties/', views.property_list, name='properties'),
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),
    path('properties/<int:property_id>/edit/', views.property_edit, name='property_edit'),
    path('properties/<int:property_id>/delete/', views.property_delete, name='property_delete'),
    path('book/<int:property_id>/', views.book_property, name='book_property'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/<int:booking_id>/accept/', views.accept_booking, name='accept_booking'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('tenants/<int:user_id>/', views.tenant_profile, name='tenant_profile'),
    path('profile/', views.profile, name='profile'),
] 

