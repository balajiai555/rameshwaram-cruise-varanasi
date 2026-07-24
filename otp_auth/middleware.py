import random
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.core.mail import send_mail

class Admin2FAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We only protect paths starting with /admin/
        if request.path.startswith('/admin/'):
            # Allow access to the custom OTP verification views and logout
            try:
                exempt_paths = [
                    reverse('admin_otp_verify'),
                    reverse('admin_otp_resend'),
                    '/admin/logout/',
                    '/admin/jsi18n/',
                ]
            except Exception:
                exempt_paths = [
                    '/admin/verify-otp/',
                    '/admin/resend-otp/',
                    '/admin/logout/',
                    '/admin/jsi18n/',
                ]
            
            if request.path in exempt_paths:
                return self.get_response(request)

            # Check if user is authenticated and is staff
            if request.user.is_authenticated and request.user.is_staff:
                # If not verified yet, generate OTP, send email, and redirect
                if not request.session.get('admin_otp_verified'):
                    otp = request.session.get('admin_otp')
                    expiry = request.session.get('admin_otp_expiry')
                    
                    if not otp or not expiry or now().timestamp() > expiry:
                        # Generate 6-digit OTP
                        otp = f"{random.randint(100000, 999999)}"
                        request.session['admin_otp'] = otp
                        request.session['admin_otp_expiry'] = now().timestamp() + 300  # 5 minutes
                        request.session.modified = True
                        
                        # Send email to the registered staff account
                        email = request.user.email
                        if email:
                            send_mail(
                                "Your Admin Panel 2FA Code",
                                f"Your one-time verification code to access the Rameshwaram Cruises Admin Panel is: {otp}\n\nThis code expires in 5 minutes.",
                                None,
                                [email],
                                fail_silently=True
                            )
                    
                    return redirect('admin_otp_verify')

        return self.get_response(request)
