from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_read', 'created_at', 'related_order']
    list_filter = ['is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['title', 'message', 'user', 'related_order', 'created_at']
