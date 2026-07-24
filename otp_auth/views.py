from django.shortcuts import render, redirect
from django.views import View
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import F
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from .models import EmailOTP
from .helpers import customer_logged_in

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class CustomerLoginView(View):
    def get(self, request):
        if customer_logged_in(request): return redirect('booking_list')
        return render(request, 'otp_auth/login.html')
    def post(self, request):
        email = (request.POST.get('email') or '').strip().lower()
        if not email or '@' not in email:
            return render(request, 'otp_auth/login.html', {'error': 'Enter a valid email', 'email': email})
        otp = EmailOTP.issue(email)
        send_mail('Your CruiseBook sign-in code',
            f'Your one-time code is {otp.code}. It expires in 10 minutes.',
            None, [email],
            html_message=render_to_string('otp_auth/email_otp.html', {'code': otp.code}),
            fail_silently=False)
        request.session['otp_pending_email'] = email
        return redirect('customer_verify')

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class CustomerVerifyView(View):
    def get(self, request):
        email = request.session.get('otp_pending_email')
        if not email: return redirect('customer_login')
        return render(request, 'otp_auth/verify.html', {'email': email})
    def post(self, request):
        email = request.session.get('otp_pending_email')
        if not email: return redirect('customer_login')
        code = (request.POST.get('code') or '').strip()
        otp = EmailOTP.objects.filter(email=email, is_used=False).order_by('-created_at').first()
        if not otp or not otp.is_valid():
            return render(request, 'otp_auth/verify.html', {'email': email, 'error': 'Code expired. Please request a new one.'})
        
        # Increment attempts counter
        EmailOTP.objects.filter(pk=otp.pk).update(attempts=F('attempts') + 1)
        otp.refresh_from_db()
        
        # Max 5 attempts allowed to prevent brute force
        if otp.attempts > 5:
            EmailOTP.objects.filter(pk=otp.pk).update(is_used=True)
            return render(request, 'otp_auth/verify.html', {'email': email, 'error': 'Too many wrong attempts. Code invalidated. Request a new one.'})
            
        if otp.code != code:
            return render(request, 'otp_auth/verify.html', {'email': email, 'error': f'Wrong code (Attempt {otp.attempts}/5). Try again.'})
            
        EmailOTP.objects.filter(pk=otp.pk).update(is_used=True)
        request.session['customer_email'] = email
        request.session.pop('otp_pending_email', None)
        request.session.set_expiry(1800)  # Expire customer session after 30 minutes of inactivity
        request.session.modified = True
        return redirect('booking_list')

class CustomerLogoutView(View):
    def get(self, request):
        request.session.pop('customer_email', None)
        request.session.pop('customer_name', None)
        request.session.pop('otp_pending_email', None)
        return redirect('home')

class AdminOTPVerifyView(View):
    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('customer_login')
        if request.session.get('admin_otp_verified'):
            return redirect('/admin/')
        email = request.user.email or "your account email"
        return render(request, 'otp_auth/admin_verify.html', {'email': email})

    def post(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('customer_login')
        
        code = (request.POST.get('code') or '').strip()
        expected_otp = request.session.get('admin_otp')
        expiry = request.session.get('admin_otp_expiry')
        email = request.user.email or "your account email"

        from django.utils.timezone import now
        if not expected_otp or not expiry or now().timestamp() > expiry:
            return render(request, 'otp_auth/admin_verify.html', {
                'email': email,
                'error': 'Verification code has expired or is invalid. Please request a new one.'
            })

        if code == expected_otp:
            request.session['admin_otp_verified'] = True
            request.session.pop('admin_otp', None)
            request.session.pop('admin_otp_expiry', None)
            request.session.modified = True
            return redirect('/admin/')
        else:
            return render(request, 'otp_auth/admin_verify.html', {
                'email': email,
                'error': 'Incorrect verification code. Please try again.'
            })

class AdminOTPResendView(View):
    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('customer_login')
        
        request.session.pop('admin_otp', None)
        request.session.pop('admin_otp_expiry', None)
        request.session.modified = True
        return redirect('/admin/')
