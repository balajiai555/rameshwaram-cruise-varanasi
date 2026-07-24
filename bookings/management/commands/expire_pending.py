from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from bookings.models import Booking
class Command(BaseCommand):
    help = 'Expire pending bookings and release their seats.'
    def handle(self, *args, **options):
        now = timezone.now()
        expired = Booking.objects.filter(status='pending', hold_expires_at__lte=now)
        count = 0
        for booking in expired:
            with transaction.atomic():
                for bs in booking.booking_seats.select_for_update().select_related('seat'):
                    if bs.seat.status in ('held', 'blocked'):
                        bs.seat.status = 'available'; bs.seat.save(update_fields=['status'])
                booking.status = 'expired'; booking.save(update_fields=['status'])
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Expired {count} pending bookings'))

