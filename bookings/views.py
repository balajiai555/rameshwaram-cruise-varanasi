import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
import razorpay
from .models import Booking, BookingSeat, Payment, IDType
from .utils import generate_booking_number, new_hold_expiry, compute_gst, compute_total, send_booking_email
from cruises.models import Schedule, Seat
from tickets.models import Ticket
from otp_auth.helpers import customer_logged_in

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class CheckoutView(View):
    def get(self, request, schedule_id):
        # Lazy cleanup of expired holds
        from django.utils import timezone
        from bookings.models import Booking
        
        expired_bookings = Booking.objects.filter(status='pending', hold_expires_at__lte=timezone.now())
        for booking in expired_bookings:
            with transaction.atomic():
                for bs in booking.booking_seats.all():
                    if bs.seat.status in ('held', 'blocked'):
                        bs.seat.status = 'available'
                        bs.seat.save(update_fields=['status'])
                booking.status = 'expired'
                booking.save(update_fields=['status'])

        from django.contrib import messages
        schedule = get_object_or_404(Schedule, pk=schedule_id, status='active')
        selected_seats = request.GET.get('seats', '')
        seat_ids = [int(s) for s in selected_seats.split(',') if s]
        if not seat_ids:
            return redirect('schedule_seats', schedule_id=schedule_id)

        # 1. Look for existing active booking in session to see if we can reuse it
        active_booking_id = request.session.get('active_booking_id')
        booking = None
        if active_booking_id:
            try:
                booking = Booking.objects.get(id=active_booking_id, schedule=schedule, status='pending')
                # Check if the seats match exactly
                existing_seat_ids = list(booking.booking_seats.values_list('seat_id', flat=True))
                if set(existing_seat_ids) == set(seat_ids):
                    # Seats match! We can reuse this booking. Refresh expiry to 7 minutes
                    booking.hold_expires_at = new_hold_expiry()
                    booking.save(update_fields=['hold_expires_at'])
                else:
                    # Seats changed. Release old booking seats
                    for bs in booking.booking_seats.all():
                        bs.seat.status = 'available'
                        bs.seat.save(update_fields=['status'])
                    booking.status = 'cancelled'
                    booking.save(update_fields=['status'])
                    booking = None
                    request.session['active_booking_id'] = None
            except Booking.DoesNotExist:
                booking = None
                request.session['active_booking_id'] = None

        # 2. If no valid existing booking, create a new temporary holding booking
        if not booking:
            # Check if all seats are available
            seats = list(Seat.objects.filter(id__in=seat_ids, schedule=schedule, status='available')
                         .order_by('row_label', 'position'))
            if len(seats) != len(seat_ids):
                messages.error(request, "Some of your selected seats are no longer available.")
                return redirect('schedule_seats', schedule_id=schedule_id)
            
            subtotal = sum(s.price for s in seats)
            total = compute_total(subtotal)
            
            with transaction.atomic():
                # Create placeholder pending booking
                booking = Booking.objects.create(
                    guest_name="Temporary Holder",
                    guest_email="temp@example.com",
                    guest_phone="0000000000",
                    guest_address="Temporary Address",
                    schedule=schedule,
                    booking_number=generate_booking_number(),
                    total_amount=total,
                    hold_expires_at=new_hold_expiry(),
                    status='pending'
                )
                
                # Mark seats as held and link to booking
                for s in seats:
                    s.status = 'held'
                    s.save(update_fields=['status'])
                    BookingSeat.objects.create(booking=booking, seat=s)
                
                request.session['active_booking_id'] = booking.id

        # 3. Retrieve held seats from the booking
        seats = [bs.seat for bs in booking.booking_seats.all().order_by('seat__row_label', 'seat__position')]
        subtotal = sum(s.price for s in seats)
        total = booking.total_amount
        
        prefill_email = request.session.get('customer_email', '') if customer_logged_in(request) else ''
        prefill_name = request.session.get('customer_name', '') if customer_logged_in(request) else ''

        return render(request, 'bookings/checkout.html', {
            'schedule': schedule, 'seats': seats,
            'subtotal': subtotal, 'gst': compute_gst(subtotal), 'total': total,
            'seat_ids': ','.join(str(s.id) for s in seats),
            'booking_id': booking.id,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'hold_minutes': settings.PENDING_BOOKING_HOLD_MINUTES,
            'prefill_email': prefill_email, 'prefill_name': prefill_name,
            'id_types': IDType.choices,
            'active_row': seats[0].row_label if seats else None,
            'debug': settings.DEBUG,
        })


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='dispatch')
class CreateOrderView(View):
    def post(self, request):
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        seat_ids = [int(s) for s in data.get('seat_ids', '').split(',') if s]

        guest_name = (data.get('guest_name') or '').strip()
        guest_email = (data.get('guest_email') or '').strip().lower()
        guest_phone = (data.get('guest_phone') or '').strip()
        guest_address = (data.get('guest_address') or '').strip()
        
        primary_name = (data.get('primary_name') or '').strip()
        primary_id_type = (data.get('primary_id_type') or '').strip()
        primary_id_number = (data.get('primary_id_number') or '').strip()
        passenger_names = [n.strip() for n in data.get('passenger_names', [])]

        if not (guest_name and guest_email and guest_phone):
            return JsonResponse({'error': 'Name, email, and phone are required'}, status=400)
        if not guest_address:
            return JsonResponse({'error': 'Billing and communication address is required'}, status=400)
        if not primary_name:
            return JsonResponse({'error': 'Primary passenger name is required'}, status=400)
        if primary_id_type not in dict(IDType.choices):
            return JsonResponse({'error': 'Invalid ID type'}, status=400)
        if not primary_id_number:
            return JsonResponse({'error': 'Primary passenger ID number is required'}, status=400)
        if len(seat_ids) == 0:
            return JsonResponse({'error': 'No seats selected'}, status=400)
        if len(passenger_names) != len(seat_ids) - 1:
            return JsonResponse({'error': f'Need {len(seat_ids) - 1} additional passenger name(s)'}, status=400)

        # Retrieve active booking from session
        active_booking_id = request.session.get('active_booking_id')
        booking = None
        if active_booking_id:
            try:
                booking = Booking.objects.get(id=active_booking_id, status='pending')
            except Booking.DoesNotExist:
                pass

        with transaction.atomic():
            if not booking:
                # Try to create a new one if seats are still available
                seats = list(Seat.objects.select_for_update().filter(
                    id__in=seat_ids, schedule_id=schedule_id, status='available'
                ))
                if len(seats) != len(seat_ids):
                    return JsonResponse({'error': 'Your seat reservation has expired and the seats are no longer available. Please select seats again.'}, status=400)
                
                subtotal = sum(s.price for s in seats)
                total = compute_total(subtotal)
                
                booking = Booking.objects.create(
                    guest_name=guest_name,
                    guest_email=guest_email,
                    guest_phone=guest_phone,
                    guest_address=guest_address,
                    schedule_id=schedule_id,
                    booking_number=generate_booking_number(),
                    total_amount=total,
                    hold_expires_at=new_hold_expiry(),
                    status='pending'
                )
                for s in seats:
                    s.status = 'held'
                    s.save(update_fields=['status'])
                    BookingSeat.objects.create(booking=booking, seat=s)
            else:
                # Update existing booking details
                booking.guest_name = guest_name
                booking.guest_email = guest_email
                booking.guest_phone = guest_phone
                booking.guest_address = guest_address
                booking.hold_expires_at = new_hold_expiry()
                booking.save()
                
                # Fetch held seats linked to this booking
                seats = [bs.seat for bs in booking.booking_seats.all()]

            existing_seat_ids = [s.id for s in seats]
            if set(existing_seat_ids) != set(seat_ids):
                return JsonResponse({'error': 'Selected seats mismatch. Please select seats again.'}, status=400)

            # Re-verify seat holds status
            held_seats = Seat.objects.select_for_update().filter(id__in=seat_ids, status='held')
            if len(held_seats) != len(seat_ids):
                # Try to re-hold available ones if they were cleared
                available_seats = Seat.objects.select_for_update().filter(id__in=seat_ids, status='available')
                if len(held_seats) + len(available_seats) != len(seat_ids):
                    return JsonResponse({'error': 'Your seat reservation has expired and the seats are no longer available. Please select seats again.'}, status=400)
                
                for s in available_seats:
                    s.status = 'held'
                    s.save(update_fields=['status'])

            # Update passenger manifest details
            booking.booking_seats.all().delete()
            seats_sorted = sorted(seats, key=lambda s: s.position)
            
            BookingSeat.objects.create(
                booking=booking, seat=seats_sorted[0], is_primary=True,
                passenger_name=primary_name, id_type=primary_id_type, id_number=primary_id_number,
            )
            for seat, name in zip(seats_sorted[1:], passenger_names):
                BookingSeat.objects.create(
                    booking=booking, seat=seat, is_primary=False, passenger_name=name,
                )

            # Check if Payment order exists or create a new one
            payment = Payment.objects.filter(booking=booking).first()
            if payment:
                order_id = payment.razorpay_order_id
                amount = int(booking.total_amount * 100)
            else:
                amount = int(booking.total_amount * 100)
                order = razorpay_client.order.create({
                    'amount': amount, 'currency': 'INR', 'receipt': booking.booking_number,
                })
                order_id = order['id']
                Payment.objects.create(booking=booking, razorpay_order_id=order_id, amount=booking.total_amount)

            return JsonResponse({
                'order_id': order_id, 'amount': amount,
                'booking_id': booking.id, 'booking_number': booking.booking_number,
                'hold_expires_at': booking.hold_expires_at.isoformat(),
            })


@method_decorator(ratelimit(key='ip', rate='30/m', method='POST', block=True), name='dispatch')
class VerifyPaymentView(View):
    def post(self, request):
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature', '')
        is_dummy = data.get('is_dummy', False)
        if not (is_dummy and settings.DEBUG):
            try:
                razorpay_client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature,
                })
            except Exception:
                return JsonResponse({'error': 'Payment verification failed'}, status=400)

        with transaction.atomic():
            payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)
            booking = payment.booking
            if booking.status == 'confirmed':
                ticket = Ticket.objects.get(booking=booking)
                return JsonResponse({'success': True,
                    'ticket_url': f'/tickets/{ticket.id}/?bn={booking.booking_number}'})

            seats = Seat.objects.select_for_update().filter(
                schedule=booking.schedule, status='held', bookingseat__booking=booking)
            for seat in seats:
                seat.status = 'booked'; seat.save(update_fields=['status'])

            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'success'; payment.save()
            booking.status = 'confirmed'; booking.save()
            ticket, _ = Ticket.objects.get_or_create(booking=booking)

            request.session['customer_email'] = booking.guest_email
            request.session['customer_name'] = booking.guest_name
            request.session.set_expiry(1800)  # Expire session after 30 minutes of inactivity
            request.session.modified = True
            send_booking_email(booking)
            return JsonResponse({'success': True,
                'ticket_url': f'/tickets/{ticket.id}/?bn={booking.booking_number}'})


@method_decorator(ratelimit(key='ip', rate='30/m', method='POST', block=True), name='dispatch')
class ReleaseBookingView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            booking_id = data.get('booking_id')
        except Exception:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        if not booking_id:
            return JsonResponse({'error': 'Booking ID is required'}, status=400)

        with transaction.atomic():
            try:
                booking = Booking.objects.select_for_update().get(pk=booking_id)
            except Booking.DoesNotExist:
                return JsonResponse({'error': 'Booking not found'}, status=404)

            # Only release if it's still pending (not confirmed or already released)
            if booking.status == 'pending':
                # Release seats
                for bs in booking.booking_seats.select_for_update().select_related('seat'):
                    if bs.seat.status in ('held', 'blocked'):
                        bs.seat.status = 'available'
                        bs.seat.save(update_fields=['status'])
                
                booking.status = 'expired'
                booking.save(update_fields=['status'])
                return JsonResponse({'success': True, 'message': 'Reservation released successfully.'})
            
            return JsonResponse({'success': False, 'message': 'Booking status is not pending.'})


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(View):
    def post(self, request):
        payload = request.body.decode('utf-8')
        signature = request.headers.get('X-Razorpay-Signature', '')
        try:
            razorpay_client.utility.verify_webhook_signature(payload, signature, settings.RAZORPAY_WEBHOOK_SECRET)
        except Exception:
            return HttpResponse('invalid signature', status=400)
        event = json.loads(payload)
        if event.get('event') == 'payment.captured':
            entity = event['payload']['payment']['entity']
            with transaction.atomic():
                try:
                    payment = Payment.objects.select_related('booking').get(razorpay_order_id=entity.get('order_id'))
                except Payment.DoesNotExist:
                    return HttpResponse('unknown order', status=200)
                if payment.status == 'success':
                    return HttpResponse('ok', status=200)
                booking = payment.booking
                seats = Seat.objects.select_for_update().filter(
                    schedule=booking.schedule, status='held', bookingseat__booking=booking)
                for seat in seats:
                    seat.status = 'booked'; seat.save(update_fields=['status'])
                payment.razorpay_payment_id = entity.get('id')
                payment.status = 'success'; payment.save()
                booking.status = 'confirmed'; booking.save()
                ticket, _ = Ticket.objects.get_or_create(booking=booking)
                send_booking_email(booking)
        return HttpResponse('ok', status=200)


class BookingListView(View):
    def get(self, request):
        if not customer_logged_in(request): return redirect('customer_login')
        email = request.session.get('customer_email', '').lower()
        bookings = (Booking.objects.filter(guest_email__iexact=email, status='confirmed')
                    .select_related('schedule__cruise').prefetch_related('booking_seats__seat')
                    .order_by('-created_at'))
        return render(request, 'bookings/list.html', {'bookings': bookings})

# File: bookings/urls.py
from django.urls import path
# pyrefly: ignore [missing-import]
from .views import CheckoutView, CreateOrderView, VerifyPaymentView, BookingListView, RazorpayWebhookView
urlpatterns = [
    path('checkout/<int:schedule_id>/', CheckoutView.as_view(), name='checkout'),
    path('api/create-order/', CreateOrderView.as_view(), name='create_order'),
    path('api/verify-payment/', VerifyPaymentView.as_view(), name='verify_payment'),
    path('api/webhook/razorpay/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),
    path('my-bookings/', BookingListView.as_view(), name='booking_list'),
]

