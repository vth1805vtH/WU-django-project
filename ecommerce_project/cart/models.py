from django.conf import settings
from django.db import models


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Cart ({self.user.username})'

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.select_related('product').all())

    @property
    def total_items(self):
        from django.db.models import Sum
        result = self.items.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    @property
    def is_empty(self):
        return self.total_items == 0


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'], name='unique_cart_product'
            )
        ]

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def effective_price(self):
        return self.product.discount_price if self.product.is_on_sale else self.product.price

    @property
    def total_price(self):
        return self.effective_price * self.quantity
