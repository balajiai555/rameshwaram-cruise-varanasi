from django.contrib import admin
from .models import Cruise, Schedule, Seat

class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    fields = ['seat_number', 'row_label', 'position', 'status', 'price']

    def get_queryset(self, request):
        from django.db.models.functions import Cast
        from django.db.models import IntegerField
        qs = super().get_queryset(request)
        return qs.annotate(
            seat_num_int=Cast('seat_number', IntegerField())
        ).order_by('seat_num_int')

@admin.register(Cruise)
class CruiseAdmin(admin.ModelAdmin):
    list_display = ['name', 'from_port', 'to_port', 'base_price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'from_port', 'to_port']

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['cruise', 'date', 'departure_time', 'status', 'available_seats_count']
    list_filter = ['status', 'date']
    inlines = [SeatInline]
    date_hierarchy = 'date'

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    """Superuser edits per-seat pricing here."""
    list_display = ['seat_number', 'row_label', 'position', 'schedule', 'status', 'price']
    list_filter = ['schedule', 'status', 'row_label']
    list_editable = ['status', 'price']  # quick inline edit on the list page
    search_fields = ['seat_number', 'row_label']

    def get_queryset(self, request):
        from django.db.models.functions import Cast
        from django.db.models import IntegerField
        qs = super().get_queryset(request)
        return qs.annotate(
            seat_num_int=Cast('seat_number', IntegerField())
        ).order_by('schedule', 'seat_num_int')
