from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.views import View
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from .forms import StaffLoginForm

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class StaffLoginView(View):
    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('dashboard')
        return render(request, 'accounts/login.html', {'form': StaffLoginForm()})
    def post(self, request):
        form = StaffLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                return render(request, 'accounts/login.html', {'form': form, 'error': 'Staff only'})
            login(request, user); return redirect('dashboard')
        return render(request, 'accounts/login.html', {'form': form})

class LogoutView(View):
    def get(self, request):
        logout(request); return redirect('home')