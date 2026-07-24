from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q, Count
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from datetime import date, timedelta
from bookings.models import Booking, Payment
from cruises.models import Cruise, Schedule, Seat

class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff: return redirect('home')
        return super().dispatch(request, *args, **kwargs)

class DashboardView(StaffRequiredMixin, View):
    def get(self, request):
        today = date.today(); week_ago = today - timedelta(days=7)
        
        # 1. Today's Revenue (default display)
        today_revenue = Payment.objects.filter(status='success', created_at__date=today).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # 2. Monthly Revenue Filter
        selected_month = request.GET.get('rev_month')
        selected_year = request.GET.get('rev_year')
        filtered_revenue = None
        filtered_label = ""
        
        if selected_month and selected_year:
            try:
                m_int = int(selected_month)
                y_int = int(selected_year)
                filtered_revenue = Payment.objects.filter(
                    status='success', 
                    created_at__year=y_int, 
                    created_at__month=m_int
                ).aggregate(Sum('amount'))['amount__sum'] or 0
                import calendar
                filtered_label = f"{calendar.month_name[m_int]} {y_int}"
            except ValueError:
                pass
                
        # Get all unique months with transactions to populate the filter dropdown
        available_months = Payment.objects.filter(status='success').dates('created_at', 'month', order='DESC')
        
        # Check active schedules missing seat assignments (fewer seats than 60)
        required_seats = 60
        schedules_missing_seats = Schedule.objects.filter(status='active').annotate(
            seat_count=Count('seats')
        ).filter(seat_count__lt=required_seats).count()

        context = {
            'today_revenue': today_revenue,
            'filtered_revenue': filtered_revenue,
            'filtered_label': filtered_label,
            'available_months': available_months,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'today_bookings': Booking.objects.filter(created_at__date=today, status='confirmed').count(),
            'total_cruises': Cruise.objects.filter(is_active=True).count(),
            'today_schedules': Schedule.objects.filter(date=today, status='active').count(),
            'recent_bookings': Booking.objects.select_related('schedule__cruise').order_by('-created_at')[:10],
            'weekly_revenue': list(Payment.objects.filter(status='success', created_at__date__gte=week_ago)
                .values('created_at__date').annotate(total=Sum('amount')).order_by('created_at__date')),
            'schedules_missing_seats': schedules_missing_seats,
        }
        return render(request, 'dashboard/index.html', context)

class InitializeSeatsView(StaffRequiredMixin, View):
    def post(self, request):
        rows = settings.DECK_ROWS
        per_row = settings.DECK_SEATS_PER_ROW
        schedules = Schedule.objects.filter(status='active')
        created = 0
        schedules_count = 0
        for schedule in schedules:
            existing_count = schedule.seats.count()
            if existing_count >= 60:
                continue
            # Rebuild schedule seats layout
            schedule.seats.all().delete()
            from cruises.utils import get_seat_layout
            layout = get_seat_layout()
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
            schedules_count += 1
            
        if created > 0:
            messages.success(request, f"Generated {created} seats across {schedules_count} schedules successfully!")
        else:
            messages.info(request, "All active schedules already have completed seat layouts.")
        return redirect('dashboard')

class BookingManageView(StaffRequiredMixin, View):
    def get(self, request):
        bookings = Booking.objects.select_related('schedule__cruise', 'ticket')
        
        q = request.GET.get('q', '').strip()
        if q:
            bookings = bookings.filter(
                Q(booking_number__icontains=q) |
                Q(guest_name__icontains=q) |
                Q(guest_phone__icontains=q) |
                Q(guest_email__icontains=q)
            )
            
        sort_by = request.GET.get('sort', 'day_asc')
        if sort_by == 'day_desc':
            bookings = bookings.order_by('-schedule__date', '-schedule__departure_time')
        elif sort_by == 'month_asc':
            bookings = bookings.order_by('schedule__date__year', 'schedule__date__month', 'schedule__date__day', 'schedule__departure_time')
        elif sort_by == 'month_desc':
            bookings = bookings.order_by('-schedule__date__year', '-schedule__date__month', '-schedule__date__day', '-schedule__departure_time')
        elif sort_by == 'booked_desc':
            bookings = bookings.order_by('-created_at')
        elif sort_by == 'booked_asc':
            bookings = bookings.order_by('created_at')
        else:
            bookings = bookings.order_by('schedule__date', 'schedule__departure_time')
            
        return render(request, 'dashboard/bookings.html', {
            'bookings': bookings,
            'q': q,
            'sort': sort_by
        })

class BookingCancelView(StaffRequiredMixin, View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, pk=booking_id)
        if booking.status == 'confirmed':
            with transaction.atomic():
                for bs in booking.booking_seats.select_for_update().select_related('seat'):
                    bs.seat.status = 'available'; bs.seat.save(update_fields=['status'])
                booking.status = 'cancelled'; booking.save()
        return redirect('dashboard_bookings')


class ScheduleManageView(StaffRequiredMixin, View):
    def get(self, request):
        today = date.today()
        # Fetch active schedules prefetching seats for performance
        schedules = Schedule.objects.filter(status='active', date__gte=today).select_related('cruise').order_by('date', 'departure_time')
        
        # Fetch active schedules pricing for display
        for s in schedules:
            first_seat = s.seats.first()
            if first_seat:
                s.price_inclusive = float(first_seat.price)
            else:
                s.price_inclusive = 700.0

        return render(request, 'dashboard/schedules.html', {
            'schedules': schedules,
            'today': today.isoformat(),
        })

    def post(self, request):
        action = request.POST.get('action')
        from datetime import datetime
        
        if action == 'generate':
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')
            time_str = request.POST.get('departure_time', '18:00')
            price_inclusive = float(request.POST.get('price', '700'))

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                departure_time = datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                messages.error(request, "Invalid date or time format. Please check your inputs.")
                return redirect('dashboard_schedules')

            if start_date > end_date:
                messages.error(request, "Start date cannot be after end date.")
                return redirect('dashboard_schedules')

            base_price = price_inclusive

            # Get the main cruise (ID 1)
            cruise = Cruise.objects.first()
            if not cruise:
                messages.error(request, "No cruise found in the database. Please create one first.")
                return redirect('dashboard_schedules')

            schedules_created = 0
            seats_created = 0
            rows = settings.DECK_ROWS
            per_row = settings.DECK_SEATS_PER_ROW

            current_date = start_date
            with transaction.atomic():
                while current_date <= end_date:
                    schedule, created = Schedule.objects.get_or_create(
                        cruise=cruise,
                        date=current_date,
                        departure_time=departure_time,
                        defaults={'status': 'active', 'total_seats': 60}
                    )
                    if created:
                        schedules_created += 1
                    else:
                        # Update price of existing schedule's seats
                        schedule.seats.all().update(price=base_price)

                    # Re-initialize seats in bulk if they are missing
                    if schedule.seats.count() < 60:
                        schedule.seats.all().delete()
                        from cruises.utils import get_seat_layout
                        layout = get_seat_layout()
                        seats_to_create = []
                        for row_idx, seat_number, row_label, position in layout:
                            seats_to_create.append(Seat(
                                schedule=schedule,
                                seat_number=seat_number,
                                row_label=row_label,
                                position=position,
                                price=base_price
                            ))
                            seats_created += 1
                        Seat.objects.bulk_create(seats_to_create)

                    current_date += timedelta(days=1)

            messages.success(request, f"Successfully created {schedules_created} schedules and initialized {seats_created} seats!")
            return redirect('dashboard_schedules')

        elif action == 'update_price':
            schedule_id = request.POST.get('schedule_id')
            price_inclusive = float(request.POST.get('new_price', '600'))

            base_price = round(price_inclusive / 1.05, 2)
            schedule = get_object_or_404(Schedule, pk=schedule_id)

            with transaction.atomic():
                updated = schedule.seats.all().update(price=base_price)
                
        elif action == 'delete':
            schedule_id = request.POST.get('schedule_id')
            schedule = get_object_or_404(Schedule, pk=schedule_id)
            if schedule.has_bookings:
                messages.error(request, f"Cannot delete schedule on {schedule.date} because it contains active bookings.")
            else:
                schedule.delete()
                messages.success(request, f"Successfully deleted schedule for {schedule.date} {schedule.departure_time}.")
            return redirect('dashboard_schedules')

        return redirect('dashboard_schedules')


class ExportBookingsCSVView(StaffRequiredMixin, View):
    def get(self, request):
        import csv
        from django.http import HttpResponse
        
        bookings = Booking.objects.select_related('schedule__cruise')
        
        q = request.GET.get('q', '').strip()
        if q:
            bookings = bookings.filter(
                Q(booking_number__icontains=q) |
                Q(guest_name__icontains=q) |
                Q(guest_phone__icontains=q) |
                Q(guest_email__icontains=q)
            )
            
        sort_by = request.GET.get('sort', 'day_asc')
        if sort_by == 'day_desc':
            bookings = bookings.order_by('-schedule__date', '-schedule__departure_time')
        elif sort_by == 'month_asc':
            bookings = bookings.order_by('schedule__date__year', 'schedule__date__month', 'schedule__date__day', 'schedule__departure_time')
        elif sort_by == 'month_desc':
            bookings = bookings.order_by('-schedule__date__year', '-schedule__date__month', '-schedule__date__day', '-schedule__departure_time')
        elif sort_by == 'booked_desc':
            bookings = bookings.order_by('-created_at')
        elif sort_by == 'booked_asc':
            bookings = bookings.order_by('created_at')
        else:
            bookings = bookings.order_by('schedule__date', 'schedule__departure_time')
            
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rameshwaram_bookings_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Booking Number', 'Guest Name', 'Guest Email', 'Guest Phone', 
            'Billing Address', 'Departure Date', 'Departure Time (24h)', 
            'Seats Booked', 'Total Amount (Rs)', 'Status', 'Booked At'
        ])
        
        for b in bookings:
            writer.writerow([
                b.booking_number,
                b.guest_name,
                b.guest_email,
                b.guest_phone,
                b.guest_address,
                b.schedule.date.strftime('%Y-%m-%d') if b.schedule else '',
                b.schedule.departure_time.strftime('%H:%M') if b.schedule else '',
                ", ".join([bs.seat.seat_number for bs in b.booking_seats.all()]),
                b.total_amount,
                b.status,
                b.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
        return response

