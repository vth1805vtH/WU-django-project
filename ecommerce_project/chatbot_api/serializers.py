from rest_framework import serializers

from .models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['role', 'content', 'timestamp']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['session_id', 'messages', 'created_at', 'updated_at']


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, min_length=1, max_length=2000)
    session_id = serializers.CharField(required=False, allow_null=True, max_length=64)


class ChatResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    reply = serializers.CharField()
    suggestions = serializers.ListField(child=serializers.CharField(), required=False)


class OrderStatusRequestSerializer(serializers.Serializer):
    order_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
