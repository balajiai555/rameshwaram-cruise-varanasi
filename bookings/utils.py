import uuid
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.conf import settings

def generate_booking_number():
    return f"CB-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def compute_gst(subtotal): return Decimal('0.00')
def compute_total(subtotal): return subtotal
def new_hold_expiry(): return timezone.now() + timezone.timedelta(minutes=settings.PENDING_BOOKING_HOLD_MINUTES)

def send_booking_email(booking):
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from tickets.models import Ticket
    try:
        ticket = booking.ticket
    except Ticket.DoesNotExist:
        return
    if not ticket: return
    base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
    subject = "Your Varanasi Ghat Cruise Yatra Ticket"
    context = {'booking': booking, 'ticket': ticket, 'base_url': base_url.rstrip('/')}
    body = render_to_string('bookings/email_ticket.txt', context)
    html = render_to_string('bookings/email_ticket.html', context)
    send_mail(subject, body, None, [booking.guest_email], html_message=html, fail_silently=True)
