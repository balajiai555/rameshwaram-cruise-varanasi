from django.urls import path
from .views import (
    CustomerLoginView, CustomerVerifyView, CustomerLogoutView,
    AdminOTPVerifyView, AdminOTPResendView
)
urlpatterns = [
    path('login/', CustomerLoginView.as_view(), name='customer_login'),
    path('verify/', CustomerVerifyView.as_view(), name='customer_verify'),
    path('logout/', CustomerLogoutView.as_view(), name='customer_logout'),
    path('admin/verify-otp/', AdminOTPVerifyView.as_view(), name='admin_otp_verify'),
    path('admin/resend-otp/', AdminOTPResendView.as_view(), name='admin_otp_resend'),
]

