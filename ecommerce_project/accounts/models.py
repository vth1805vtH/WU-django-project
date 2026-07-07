from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Laptop(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cpu = models.CharField(max_length=100)
    ram = models.CharField(max_length=50)
    storage = models.CharField(max_length=50)
    graphics = models.CharField(max_length=100)
    display = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    keyboard = models.CharField(max_length=100)
    battery = models.CharField(max_length=50)
    weight = models.CharField(max_length=50)
    warranty = models.CharField(max_length=50)
    image = models.ImageField(upload_to='laptops/')
    discount = models.IntegerField(default=0)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username}\'s profile'


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses',
    )
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    province_or_state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.address_line_1}, {self.city}'

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    qr_code = models.ImageField(upload_to='payment_qrcodes/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
