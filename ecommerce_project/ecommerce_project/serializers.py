from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import Address, CustomerProfile, PaymentMethod
from cart.models import Cart, CartItem
from dashboard.models import Notification
from orders.models import Order, OrderItem
from products.models import Brand, Category, Product

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ['id', 'user', 'phone_number', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image']
        read_only_fields = ['id', 'slug']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='name', read_only=True)
    brand = serializers.SlugRelatedField(slug_field='name', read_only=True)
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'brand', 'name', 'slug', 'price',
            'discount_price', 'stock', 'image', 'is_active',
            'is_on_sale', 'discount_percentage', 'average_rating',
            'review_count', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'brand', 'name', 'slug', 'description',
            'price', 'discount_price', 'stock', 'image', 'is_active',
            'is_on_sale', 'discount_percentage', 'average_rating',
            'review_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    effective_price = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'quantity',
            'effective_price', 'total_price',
        ]
        read_only_fields = ['id']

    def validate_product_id(self, value):
        from products.models import Product
        if not Product.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError('Product not found or inactive.')
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()
    is_empty = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'total_items', 'is_empty', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'full_name', 'phone_number', 'address_line_1',
            'address_line_2', 'city', 'province_or_state',
            'postal_code', 'country', 'is_default', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_is_default(self, value):
        return value


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'slug', 'description', 'qr_code', 'is_active']
        read_only_fields = ['id', 'slug']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'total_price']
        read_only_fields = ['id']


class OrderListSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    payment_method_name = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'total_amount', 'status',
            'payment_status', 'payment_method', 'payment_method_name',
            'item_count', 'created_at',
        ]
        read_only_fields = ['id', 'order_number', 'created_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    payment_method_name = serializers.ReadOnlyField()
    payment_method = PaymentMethodSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'total_amount', 'status',
            'payment_status', 'payment_method', 'payment_method_name',
            'shipping_address', 'phone_number',
            'first_name', 'last_name', 'email',
            'address', 'city', 'postal_code', 'country',
            'item_count', 'items', 'created_at',
        ]
        read_only_fields = ['id', 'order_number', 'user', 'created_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'total_amount', 'status',
            'payment_status', 'payment_method',
            'phone_number', 'shipping_address',
            'first_name', 'last_name', 'email',
            'address', 'city', 'postal_code', 'country',
            'items', 'created_at',
        ]
        read_only_fields = [
            'id', 'order_number', 'status', 'payment_status',
            'items', 'created_at',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'related_order', 'created_at']
        read_only_fields = ['id', 'created_at']
