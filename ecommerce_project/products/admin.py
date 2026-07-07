from django.contrib import admin
from django.utils.html import format_html

from .models import Brand, Category, Product


class ImagePreviewMixin:
    def _get_image(self, obj):
        return getattr(obj, 'image', None) or getattr(obj, 'logo', None)

    def image_preview(self, obj):
        img = self._get_image(obj)
        if img:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;" />',
                img.url,
            )
        return '—'
    image_preview.short_description = 'Image'

    def image_preview_large(self, obj):
        img = self._get_image(obj)
        if img:
            return format_html(
                '<img src="{}" style="max-width:300px;max-height:300px;object-fit:contain;" />',
                img.url,
            )
        return '—'
    image_preview_large.short_description = 'Image Preview'


class BrandAdmin(ImagePreviewMixin, admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'slug', 'image_preview', 'product_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    readonly_fields = ['image_preview_large', 'created_at']

    fieldsets = [
        (None, {
            'fields': ['name', 'slug', 'logo', 'image_preview_large'],
        }),
        ('Timestamps', {
            'fields': ['created_at'],
        }),
    ]

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class CategoryAdmin(ImagePreviewMixin, admin.ModelAdmin):
    search_fields = ['name', 'description']
    list_display = ['name', 'slug', 'image_preview']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    readonly_fields = ['image_preview_large']

    fieldsets = [
        (None, {
            'fields': ['name', 'slug', 'description', 'image', 'image_preview_large'],
        }),
    ]

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductAdmin(ImagePreviewMixin, admin.ModelAdmin):
    search_fields = ['name', 'description', 'category__name', 'brand__name']
    list_display = [
        'name', 'category', 'brand', 'price', 'discount_price', 'stock',
        'is_active', 'is_on_sale', 'image_preview', 'created_at',
    ]
    list_filter = ['category', 'brand', 'is_active', 'created_at']
    list_editable = ['is_active', 'stock', 'price']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-created_at']
    list_select_related = ['category', 'brand']
    readonly_fields = ['image_preview_large']

    fieldsets = [
        (None, {
            'fields': ['category', 'brand', 'name', 'slug', 'description', 'price', 'discount_price', 'stock', 'image', 'image_preview_large', 'is_active'],
        }),
    ]

    def is_on_sale(self, obj):
        return obj.is_on_sale
    is_on_sale.boolean = True
    is_on_sale.short_description = 'On Sale'


admin.site.register(Brand, BrandAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
