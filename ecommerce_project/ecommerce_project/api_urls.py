from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import api_views

app_name = 'api'

urlpatterns = [
    # Auth
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Search
    path('search/', api_views.SmartSearchView.as_view(), name='smart_search'),

    # Products
    path('products/', api_views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', api_views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/recommendations/', api_views.ProductRecommendationsView.as_view(), name='product_recommendations'),

    # Categories
    path('categories/', api_views.CategoryListView.as_view(), name='category_list'),

    # Brands
    path('brands/', api_views.BrandListView.as_view(), name='brand_list'),

    # Cart
    path('cart/', api_views.CartDetailView.as_view(), name='cart_detail'),
    path('cart/add/', api_views.CartAddView.as_view(), name='cart_add'),
    path('cart/update/', api_views.CartUpdateView.as_view(), name='cart_update'),
    path('cart/remove/', api_views.CartRemoveView.as_view(), name='cart_remove'),

    # Orders
    path('orders/', api_views.OrderListView.as_view(), name='order_list'),
    path('orders/create/', api_views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', api_views.OrderDetailView.as_view(), name='order_detail'),

    # Addresses
    path('addresses/', api_views.AddressListView.as_view(), name='address_list'),
    path('addresses/<int:pk>/', api_views.AddressDetailView.as_view(), name='address_detail'),

    # Notifications
    path('notifications/', api_views.NotificationListView.as_view(), name='notification_list'),

    # Chat
    path('', include('chatbot_api.api_urls')),
]
