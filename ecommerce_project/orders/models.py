import uuid
from datetime import datetime

from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    phone_number = models.CharField(max_length=20, default='')
    shipping_address = models.TextField(blank=True, default='')
    payment_method = models.ForeignKey(
        'accounts.PaymentMethod',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders',
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    first_name = models.CharField(max_length=100, default='')
    last_name = models.CharField(max_length=100, default='')
    email = models.EmailField(default='')
    address = models.CharField(max_length=255, default='')
    city = models.CharField(max_length=100, default='')
    postal_code = models.CharField(max_length=20, default='')
    country = models.CharField(max_length=100, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.order_number}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_part = datetime.now().strftime('%Y%m%d')
            unique_part = uuid.uuid4().hex[:8].upper()
            self.order_number = f'{date_part}{unique_part}'
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        from django.db.models import Sum
        result = self.items.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    @property
    def payment_method_name(self):
        return self.payment_method.name if self.payment_method else '—'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.SET_NULL, null=True, related_name='order_items'
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.quantity} x {self.product.name if self.product else "Deleted Product"}'

    @property
    def total_price(self):
        return self.price * self.quantity
