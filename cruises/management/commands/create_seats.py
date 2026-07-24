from django.core.management.base import BaseCommand
from django.conf import settings
from cruises.models import Schedule, Seat
from cruises.utils import get_seat_layout

class Command(BaseCommand):
    help = 'Create 60 seats (R1..R8 variable) for all active schedules that need them.'

    def handle(self, *args, **options):
        schedules = Schedule.objects.filter(status='active')
        created = 0
        layout = get_seat_layout()
        
        for schedule in schedules:
            existing_count = schedule.seats.count()
            # If the schedule already has 60 seats, it's complete
            if existing_count >= 60:
                continue
            # Wipe and rebuild if partial
            schedule.seats.all().delete()
            
            seats_to_create = []
            for row_idx, seat_number, row_label, position in layout:
                seats_to_create.append(Seat(
                    schedule=schedule,
                    seat_number=seat_number,
                    row_label=row_label,
                    position=position,
                    price=schedule.cruise.base_price,
                ))
                created += 1
            Seat.objects.bulk_create(seats_to_create)
            
        self.stdout.write(self.style.SUCCESS(f'Created {created} seats across {schedules.count()} schedules'))
