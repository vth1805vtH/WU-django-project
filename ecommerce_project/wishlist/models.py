from django.conf import settings
from django.db import models


class Wishlist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}\'s Wishlist'

    @property
    def total_items(self):
        return self.items.count()


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='wishlist_items'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['wishlist', 'product'], name='unique_wishlist_product'
            )
        ]

    def __str__(self):
        return self.product.name
