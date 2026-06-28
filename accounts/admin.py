from django.contrib import admin
from .models import OTP


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'purpose', 'is_used', 'created_at')
    list_filter = ('purpose', 'is_used')
    search_fields = ('email',)
    ordering = ('-created_at',)