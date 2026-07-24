from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Booking, BookingSeat, Payment
class BookingSeatInline(admin.TabularInline):
    model = BookingSeat; extra = 0
    fields = ['seat', 'is_primary', 'passenger_name', 'id_type', 'id_number']
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_number', 'guest_name', 'guest_email', 'guest_phone',
                    'schedule', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['booking_number', 'guest_email', 'guest_phone', 'guest_name']
    inlines = [BookingSeatInline]
    readonly_fields = ['booking_number', 'hold_expires_at', 'created_at', 'updated_at']
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'razorpay_order_id', 'amount', 'status', 'created_at']
    list_filter = ['status']
