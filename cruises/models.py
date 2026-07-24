# File: cruises/models.py
from django.db import models
from django.conf import settings

class Cruise(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='cruises/', blank=True)
    description = models.TextField()
    from_port = models.CharField(max_length=100)
    to_port = models.CharField(max_length=100)
    duration_hours = models.PositiveIntegerField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)  # default per-seat price
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'cruises'; ordering = ['-created_at']
    def __str__(self):
        return f"{self.name} ({self.from_port} → {self.to_port})"
class Schedule(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('cancelled', 'Cancelled'), ('completed', 'Completed')]
    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    departure_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    # Total = DECK_ROWS * DECK_SEATS_PER_ROW (60 by default)
    total_seats = models.PositiveIntegerField(default=settings.DECK_ROWS * settings.DECK_SEATS_PER_ROW)
    class Meta:
        db_table = 'schedules'; ordering = ['date', 'departure_time']
        unique_together = ['cruise', 'date', 'departure_time']
    def __str__(self):
        return f"{self.cruise.name} - {self.date} {self.departure_time}"
    @property
    def available_seats_count(self):
        return self.seats.filter(status='available').count()
    @property
    def has_bookings(self):
        return self.bookings.filter(status__in=['confirmed', 'pending']).exists()

class Seat(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('blocked', 'Blocked'),
        ('held', 'Held (awaiting payment)'),
    ]
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)   # 1..60 flat numbering
    row_label = models.CharField(max_length=10, db_index=True)  # R1..R10
    position = models.PositiveSmallIntegerField()   # 1..6 within row
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    price = models.DecimalField(max_digits=10, decimal_places=2)  # superuser-editable
    class Meta:
        db_table = 'seats'
        unique_together = ['schedule', 'seat_number']
        ordering = ['seat_number']
    def __str__(self):
        return f"{self.seat_number} ({self.row_label}, seat {self.position})"
