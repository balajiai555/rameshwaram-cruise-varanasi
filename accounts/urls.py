from django.urls import path
from .views import StaffLoginView, LogoutView
urlpatterns = [
    path('login/', StaffLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
