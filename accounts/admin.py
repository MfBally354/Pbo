# accounts/admin.py
from django.contrib import admin
from .models import User, RestaurantProfile, DriverProfile, CustomerProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('username','email','role','is_approved','is_staff','is_superuser')
    list_filter = ('role','is_approved','is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Approval', {'fields': ('role','is_approved')}),
    )
    actions = ['approve_users']

    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} akun telah disetujui.")
    approve_users.short_description = "Setujui akun terpilih"

admin.site.register(User, UserAdmin)
admin.site.register(RestaurantProfile)
admin.site.register(DriverProfile)
admin.site.register(CustomerProfile)
