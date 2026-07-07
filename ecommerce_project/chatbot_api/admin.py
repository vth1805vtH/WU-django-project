from django.contrib import admin

from .models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['role', 'content', 'timestamp']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'short_content', 'timestamp']
    list_filter = ['role', 'timestamp']
    search_fields = ['content']

    def short_content(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    short_content.short_description = 'Content'
