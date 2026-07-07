from django.urls import path

from . import api_views

urlpatterns = [
    # Legacy chat endpoint (backward compatible)
    path('chat/', api_views.ChatView.as_view(), name='chat'),

    # New assistant API endpoints
    path('assistant/chat/', api_views.ChatView.as_view(), name='assistant_chat'),
    path('assistant/history/', api_views.ChatHistoryView.as_view(), name='assistant_history'),
    path('assistant/recommendations/', api_views.RecommendationsView.as_view(), name='assistant_recommendations'),
    path('assistant/order-status/', api_views.OrderStatusView.as_view(), name='assistant_order_status'),
    path('assistant/suggestions/', api_views.ProductSuggestionsView.as_view(), name='assistant_suggestions'),
]
