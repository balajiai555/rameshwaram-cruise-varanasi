from django.urls import path
from .views import TicketDetailView, TicketPDFView, QRScannerView, VerifyQRView
urlpatterns = [
    path('<int:ticket_id>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('<int:ticket_id>/pdf/', TicketPDFView.as_view(), name='ticket_pdf'),
    path('scanner/', QRScannerView.as_view(), name='qr_scanner'),
    path('api/verify/', VerifyQRView.as_view(), name='verify_qr'),
]
