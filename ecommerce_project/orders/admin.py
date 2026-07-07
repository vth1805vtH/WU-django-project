from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'total_amount',
        'item_count', 'created_at',
    ]
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    search_fields = ['order_number', 'user__username', 'user__email']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'total_amount', 'user', 'created_at']
    date_hierarchy = 'created_at'
