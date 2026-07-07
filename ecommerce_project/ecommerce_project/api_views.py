from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Address, CustomerProfile
from cart.models import Cart, CartItem
from dashboard.models import Notification
from orders.models import Order, OrderItem
from products.models import Brand, Category, Product
from products.services.recommendation_service import get_recommendations
from products.services.search_service import smart_search

from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from . import serializers

User = get_user_model()


# --- Products ---

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = serializers.ProductListSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['name', 'description']
    filterset_fields = ['category__slug', 'brand__slug']


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = serializers.ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class ProductRecommendationsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)
        recommendations = get_recommendations(product)
        serializer = serializers.ProductListSerializer(recommendations, many=True)
        return Response(serializer.data)


class SmartSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({'results': [], 'query': ''})

        products = smart_search(query)
        serializer = serializers.ProductListSerializer(products, many=True)
        return Response({'results': serializer.data, 'query': query})


# --- Categories ---

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [permissions.AllowAny]


# --- Brands ---

class BrandListView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = serializers.BrandSerializer
    permission_classes = [permissions.AllowAny]


# --- Cart ---

class CartDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = serializers.CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data.get('quantity', 1)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={'quantity': quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        out_serializer = serializers.CartSerializer(cart)
        return Response(out_serializer.data, status=status.HTTP_200_OK)


class CartUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')

        if not item_id:
            return Response({'error': 'item_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        if quantity is not None and int(quantity) > 0:
            cart_item.quantity = int(quantity)
            cart_item.save()
        else:
            cart_item.delete()

        out_serializer = serializers.CartSerializer(cart)
        return Response(out_serializer.data, status=status.HTTP_200_OK)


class CartRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item_id = request.data.get('item_id')

        if not item_id:
            return Response({'error': 'item_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        out_serializer = serializers.CartSerializer(cart)
        return Response(out_serializer.data, status=status.HTTP_200_OK)


# --- Orders ---

class OrderListView(generics.ListAPIView):
    serializer_class = serializers.OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderCreateView(generics.CreateAPIView):
    serializer_class = serializers.OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if cart.is_empty:
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        address_id = request.data.get('address_id')
        payment_method_id = request.data.get('payment_method_id')

        shipping_address = ''
        if address_id:
            try:
                addr = Address.objects.get(id=address_id, user=request.user)
                shipping_address = str(addr)
            except Address.DoesNotExist:
                pass

        order = Order.objects.create(
            user=request.user,
            total_amount=cart.total_price,
            shipping_address=shipping_address,
            payment_method_id=payment_method_id,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            email=request.data.get('email', ''),
            phone_number=request.data.get('phone_number', ''),
            address=request.data.get('address', ''),
            city=request.data.get('city', ''),
            postal_code=request.data.get('postal_code', ''),
            country=request.data.get('country', ''),
        )

        for cart_item in cart.items.select_related('product').all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.effective_price,
            )

        cart.items.all().delete()

        Notification.objects.create(
            user=request.user,
            title='Order Placed',
            message=f'Your order #{order.order_number} has been placed successfully.',
            related_order=order,
        )

        serializer = serializers.OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


# --- Addresses ---

class AddressListView(generics.ListCreateAPIView):
    serializer_class = serializers.AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


# --- Notifications ---

class NotificationListView(generics.ListAPIView):
    serializer_class = serializers.NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


# --- Bootstrap (one-time setup for Render) ---

import os
from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def bootstrap_view(request):
    expected_key = os.environ.get('BOOTSTRAP_KEY', '')
    provided_key = request.GET.get('key', '')

    if not expected_key or provided_key != expected_key:
        return JsonResponse({'error': 'Invalid or missing bootstrap key'}, status=403)

    results = []

    admin_username = os.environ.get('ADMIN_USERNAME', '')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', '')

    if admin_username and admin_password:
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(admin_username, admin_email, admin_password)
            results.append(f'Superuser "{admin_username}" created')
        else:
            results.append(f'Superuser "{admin_username}" already exists')

    try:
        call_command('loaddata', 'products.json')
        results.append('Products fixture loaded')
    except Exception as e:
        results.append(f'Fixture error: {e}')

    return JsonResponse({'status': 'done', 'results': results})
