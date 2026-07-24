from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
import uuid

def ticket_qr_path(instance, filename): return f'tickets/qr/{instance.ticket_number}.png'
def ticket_pdf_path(instance, filename): return f'tickets/pdf/{instance.ticket_number}.pdf'

class Ticket(models.Model):
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='ticket')
    ticket_number = models.CharField(max_length=30, unique=True)
    qr_code = models.ImageField(upload_to=ticket_qr_path, blank=True)
    pdf = models.FileField(upload_to=ticket_pdf_path, blank=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'tickets'
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
        if not self.qr_code: self.generate_qr()
    def generate_qr(self):
        # QR encodes the booking_number — used as customer secret + boarding scan
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(self.booking.booking_number)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO(); img.save(buffer, format='PNG')
        self.qr_code.save(f'{self.ticket_number}.png', File(buffer), save=True)

