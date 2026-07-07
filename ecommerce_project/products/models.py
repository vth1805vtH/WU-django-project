from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.utils.text import slugify


class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products'
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name='products', null=True, blank=True
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_on_sale(self):
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale and self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def average_rating(self):
        result = self.reviews.aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] else 0

    @property
    def review_count(self):
        return self.reviews.count()


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'], name='unique_product_review'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.rating})'


class RecentlyViewed(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recently_viewed',
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='recently_viewed_by'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'], name='unique_user_recently_viewed'
            )
        ]

    def __str__(self):
        return f'{self.user.username} viewed {self.product.name}'
