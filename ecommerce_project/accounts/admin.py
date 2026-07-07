from django.contrib import admin
from django.utils.html import format_html

from .models import Address, CustomerProfile, Laptop, PaymentMethod


@admin.register(Laptop)
class LaptopAdmin(admin.ModelAdmin):
    pass


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'created_at']
    search_fields = ['user__username', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'country', 'is_default']
    list_filter = ['is_default', 'country']
    search_fields = ['full_name', 'user__username', 'city']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'qr_code_preview']
    list_filter = ['is_active']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['qr_code_preview']

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.qr_code.url
            )
        return "No QR code"

    qr_code_preview.short_description = 'QR Code'
