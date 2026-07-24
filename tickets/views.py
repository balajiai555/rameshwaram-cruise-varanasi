from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from django.db.models import Q
from .models import Ticket
from django.template.loader import render_to_string
from django.utils import timezone
from otp_auth.helpers import customer_logged_in

def _customer_can_view(request, booking):
    if request.user.is_authenticated and request.user.is_staff:
        return True
    bn = request.GET.get('bn', '').strip()
    if bn and bn == booking.booking_number: return True
    if customer_logged_in(request):
        email = request.session.get('customer_email', '').lower()
        if email and email == booking.guest_email.lower(): return True
    return False

class TicketDetailView(View):
    def get(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        if not _customer_can_view(request, ticket.booking): return redirect('customer_login')
        return render(request, 'tickets/detail.html', {'ticket': ticket})

class TicketPDFView(View):
    def get(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        if not _customer_can_view(request, ticket.booking):
            return HttpResponse('Unauthorized', status=401)

        # Calculate tax breakdown (5% GST inclusive: 2.5% CGST + 2.5% SGST)
        import os
        from django.conf import settings
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
        if not os.path.exists(logo_path):
            logo_path = None

        total_amount = float(ticket.booking.total_amount)
        base_fare = total_amount
        cgst = 0.0
        sgst = 0.0
        gst_total = 0.0

        html = render_to_string('tickets/pdf_templates.html', {
            'ticket': ticket,
            'logo_path': logo_path,
            'base_fare': f"{base_fare:.2f}",
            'cgst': f"{cgst:.2f}",
            'sgst': f"{sgst:.2f}",
            'gst_total': f"{gst_total:.2f}"
        })

        # Check if native dependencies for WeasyPrint are available on Windows
        import ctypes.util
        import os
        
        weasyprint_supported = True
        if os.name == 'nt':
            lib_gobject = ctypes.util.find_library('libgobject-2.0-0') or ctypes.util.find_library('gobject-2.0')
            if not lib_gobject:
                weasyprint_supported = False

        # Try generating using WeasyPrint first
        if weasyprint_supported:
            try:
                from weasyprint import HTML
                pdf = HTML(string=html).write_pdf()
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{ticket.ticket_number}.pdf"'
                return response
            except Exception:
                pass

        # Fallback to pure Python xhtml2pdf (requires no native GObject/Pango libraries)
        try:
            from xhtml2pdf import pisa
            from io import BytesIO
            result = BytesIO()
            pisa_status = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
            if not pisa_status.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{ticket.ticket_number}.pdf"'
                return response
        except Exception as e:
            pass

        return HttpResponse(
            'PDF generation is currently unavailable on this server.',
            status=503
        )

class QRScannerView(View):
    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_staff: return redirect('home')
        return render(request, 'tickets/scanner.html')

class VerifyQRView(View):
    def post(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return HttpResponse('Unauthorized', status=403)
        import json
        data = json.loads(request.body)
        scanned = (data.get('ticket_number') or '').strip()
        if not scanned: return HttpResponse('Empty scan', status=400)
        ticket = Ticket.objects.filter(
            Q(ticket_number=scanned) | Q(booking__booking_number=scanned)
        ).select_related('booking').first()
        if not ticket: return HttpResponse('Invalid', status=404)
        if ticket.is_used: return HttpResponse('Already used', status=400)
        ticket.is_used = True; ticket.used_at = timezone.now(); ticket.save()
        return HttpResponse('Verified')

