from django.urls import path

from .views import (
    CheckoutView,
    CreateOrderView,
    VerifyPaymentView,
    BookingListView,
    RazorpayWebhookView,
    ReleaseBookingView,
)

urlpatterns = [
    path('checkout/<int:schedule_id>/', CheckoutView.as_view(), name='checkout'),
    path('api/create-order/', CreateOrderView.as_view(), name='create_order'),
    path('api/verify-payment/', VerifyPaymentView.as_view(), name='verify_payment'),
    path('api/release-booking/', ReleaseBookingView.as_view(), name='release_booking'),
    path('api/webhook/razorpay/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),
    path('my-bookings/', BookingListView.as_view(), name='booking_list'),
]
