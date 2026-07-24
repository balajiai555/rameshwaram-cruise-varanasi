from django.db import models
from django.conf import settings
from django.utils import timezone

class IDType(models.TextChoices):
    AADHAAR = 'aadhaar', 'Aadhaar'
    PAN = 'pan', 'PAN'
    PASSPORT = 'passport', 'Passport'
    OTHER = 'other', 'Other'

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'), ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'), ('failed', 'Failed'), ('expired', 'Expired'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             related_name='bookings', null=True, blank=True)
    schedule = models.ForeignKey('cruises.Schedule', on_delete=models.CASCADE, related_name='bookings')
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField(db_index=True)
    guest_phone = models.CharField(max_length=15, db_index=True)
    guest_address = models.TextField(default="")
    booking_number = models.CharField(max_length=20, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    hold_expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'bookings'; ordering = ['-created_at']
        indexes = [models.Index(fields=['guest_email']),
                   models.Index(fields=['status', 'hold_expires_at'])]
    def __str__(self):
        return self.booking_number
    def is_expired(self):
        return self.status == 'pending' and timezone.now() >= self.hold_expires_at
    @property
    def primary_passenger(self):
        return self.booking_seats.filter(is_primary=True).first()

class BookingSeat(models.Model):
    """One row per seat. Primary carries name + ID; rest carry name only."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_seats')
    seat = models.ForeignKey('cruises.Seat', on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    passenger_name = models.CharField(max_length=100)
    id_type = models.CharField(max_length=20, choices=IDType.choices, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    class Meta:
        db_table = 'booking_seats'
        unique_together = ['booking', 'seat']
        ordering = ['is_primary', 'id']

class Payment(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('success', 'Success'),
                      ('failed', 'Failed'), ('refunded', 'Refunded')]
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'payments'
