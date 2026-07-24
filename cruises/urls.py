from django.urls import path
from .views import HomeView, CruiseDetailView, ScheduleSeatsView, PrivacyPolicyView
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('cruise/<int:pk>/', CruiseDetailView.as_view(), name='cruise_detail'),
    path('schedule/<int:schedule_id>/seats/', ScheduleSeatsView.as_view(), name='schedule_seats'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
]
