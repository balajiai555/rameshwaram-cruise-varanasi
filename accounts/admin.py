from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'phone', 'is_staff']
    list_filter = ['is_staff', 'is_active']
    fieldsets = [(None, {'fields': ['email', 'password']}), ('Personal', {'fields': ['full_name', 'phone']}),
                 ('Permissions', {'fields': ['is_staff', 'is_active', 'groups', 'user_permissions']})]
    add_fieldsets = [(None, {'classes': ['wide'], 'fields': ['email', 'full_name', 'phone', 'password1', 'password2']})]
    search_fields = ['email', 'full_name', 'phone']; ordering = ['email']

