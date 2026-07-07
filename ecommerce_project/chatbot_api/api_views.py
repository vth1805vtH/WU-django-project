import uuid

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, ChatSession
from .serializers import (
    ChatMessageSerializer,
    ChatRequestSerializer,
    OrderStatusRequestSerializer,
)
from .services.ai_assistant import SUGGESTED_QUESTIONS, process_message
from .services.order_assistant import get_user_orders, format_orders
from .services.recommendation_engine import (
    format_recommendations,
    get_personalized_recommendations,
)


class ChatView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'assistant'

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')

        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(
                    session_id=str(uuid.uuid4().hex),
                    user=user,
                )
                session_id = session.session_id
        else:
            session = ChatSession.objects.create(
                session_id=str(uuid.uuid4().hex),
                user=user,
            )
            session_id = session.session_id

        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content=message
        )

        history_qs = list(
            ChatMessage.objects.filter(session=session)
            .exclude(role=ChatMessage.Role.SYSTEM)
            .order_by('timestamp')
        )
        history_data = [{'role': m.role, 'content': m.content} for m in history_qs]

        reply = process_message(
            user=request.user if request.user.is_authenticated else None,
            message=message,
            history=history_data,
        )

        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.ASSISTANT, content=reply
        )

        return Response({
            'session_id': session_id,
            'reply': reply,
            'suggestions': SUGGESTED_QUESTIONS,
        })


class ChatHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user)[:10]
        data = []
        for s in sessions:
            messages = list(s.messages.all()[:50])
            data.append({
                'session_id': s.session_id,
                'messages': ChatMessageSerializer(messages, many=True).data,
                'created_at': s.created_at.isoformat(),
            })
        return Response({'sessions': data})


class RecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        products = get_personalized_recommendations(request.user, 5)
        reply = format_recommendations(products, title='Recommended for You')
        return Response({'reply': reply})


class OrderStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = OrderStatusRequestSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        order_number = serializer.validated_data.get('order_number', '')
        if order_number:
            from .services.order_assistant import get_order_by_number, format_order_detail
            order = get_order_by_number(request.user, order_number.upper())
            if order:
                return Response({'reply': format_order_detail(order)})
            return Response(
                {'reply': f"I couldn't find order #{order_number}. Please check your order number."},
                status=status.HTTP_404_NOT_FOUND,
            )

        orders = get_user_orders(request.user)
        reply = format_orders(orders)
        return Response({'reply': reply})


class ProductSuggestionsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .services.search_engine import search_suggestions
        query = request.GET.get('q', '').strip()
        results = search_suggestions(query)
        return Response({'results': results})
