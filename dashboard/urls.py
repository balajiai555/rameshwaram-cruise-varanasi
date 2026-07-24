from django.urls import path
from .views import DashboardView, BookingManageView, BookingCancelView, InitializeSeatsView, ScheduleManageView, ExportBookingsCSVView
urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('bookings/', BookingManageView.as_view(), name='dashboard_bookings'),
    path('bookings/<int:booking_id>/cancel/', BookingCancelView.as_view(), name='dashboard_booking_cancel'),
    path('bookings/export/', ExportBookingsCSVView.as_view(), name='dashboard_bookings_export'),
    path('init-seats/', InitializeSeatsView.as_view(), name='dashboard_init_seats'),
    path('schedules/', ScheduleManageView.as_view(), name='dashboard_schedules'),
]
