from django.shortcuts import render, get_object_or_404
from django.views import View
from django.db.models import Q
from .models import Cruise, Schedule, Seat
from datetime import date

class HomeView(View):
    def get(self, request):
        from datetime import date, timedelta
        cruises = Cruise.objects.filter(is_active=True).prefetch_related('schedules')
        selected_date_str = request.GET.get('date', '').strip()
        selected_date = None
        if selected_date_str:
            try:
                selected_date = date.fromisoformat(selected_date_str)
            except (ValueError, TypeError):
                selected_date = None

        # Filter cruises by date: show cruise only if it has a schedule on the selected date
        if selected_date:
            cruise_ids_with_schedule = Schedule.objects.filter(
                date=selected_date, status='active'
            ).values_list('cruise_id', flat=True)
            cruises = cruises.filter(id__in=list(cruise_ids_with_schedule))

        # Annotate each cruise with next 7 upcoming dates and the next schedule
        today = date.today()
        tomorrow = today + timedelta(days=1)
        week_ahead = today + timedelta(days=30)
        cruise_data = []
        for cruise in cruises:
            upcoming = list(
                cruise.schedules.filter(date__gte=today, status='active')
                .order_by('date').values_list('date', flat=True).distinct()
            )
            next_sched = None
            if selected_date:
                next_sched = cruise.schedules.filter(date=selected_date, status='active').order_by('departure_time').first()
            if not next_sched:
                next_sched = cruise.schedules.filter(date__gte=today, status='active').order_by('date', 'departure_time').first()
            
            if next_sched:
                first_seat = next_sched.seats.first()
                if first_seat:
                    next_sched.price = first_seat.price
                else:
                    next_sched.price = cruise.base_price

            cruise.upcoming_dates = upcoming
            cruise.next_schedule = next_sched
            cruise_data.append(cruise)

        return render(request, 'cruises/home.html', {
            'cruises': cruise_data,
            'selected_date': selected_date,
            'today': today,
            'tomorrow': tomorrow,
        })

class CruiseDetailView(View):
    def get(self, request, pk):
        cruise = get_object_or_404(Cruise, pk=pk, is_active=True)
        schedules = cruise.schedules.filter(date__gte=date.today(), status='active')
        return render(request, 'cruises/detail.html', {'cruise': cruise, 'schedules': schedules})

class ScheduleSeatsView(View):
    def get(self, request, schedule_id):
        # Lazy cleanup of expired holds
        from django.utils import timezone
        from bookings.models import Booking
        from django.db import transaction
        
        expired_bookings = Booking.objects.filter(status='pending', hold_expires_at__lte=timezone.now())
        for booking in expired_bookings:
            with transaction.atomic():
                for bs in booking.booking_seats.all():
                    if bs.seat.status in ('held', 'blocked'):
                        bs.seat.status = 'available'
                        bs.seat.save(update_fields=['status'])
                booking.status = 'expired'
                booking.save(update_fields=['status'])

        schedule = get_object_or_404(Schedule, pk=schedule_id, status='active')
        # Cast Substring of row_label starting at index 2 (removing 'R') to Integer to sort rows numerically (R1..R8)
        from django.db.models.functions import Cast, Substr
        from django.db.models import IntegerField
        seats = schedule.seats.annotate(
            row_num=Cast(Substr('row_label', 2), IntegerField())
        ).order_by('row_num', 'position')

        grid_rows = []
        for row_idx in range(1, 9):
            row_label = f"R{row_idx}"
            row_seats = seats.filter(row_label=row_label)
            
            row_cells = []
            for pos in range(1, 10):
                if pos == 5:
                    row_cells.append({'type': 'walkway'})
                else:
                    seat = row_seats.filter(position=pos).first()
                    if seat:
                        row_cells.append({'type': 'seat', 'data': seat})
                    else:
                        row_cells.append({'type': 'empty'})
            
            grid_rows.append({
                'label': row_label,
                'cells': row_cells
            })

        return render(request, 'cruises/seats.html', {
            'schedule': schedule, 
            'seats': seats,
            'grid_rows': grid_rows
        })


class PrivacyPolicyView(View):
    def get(self, request):
        return render(request, 'cruises/privacy_policy.html')


def custom_page_not_found_view(request, exception=None):
    return render(request, '404.html', status=404)

