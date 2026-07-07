from django.contrib import admin

from .models import Wishlist, WishlistItem


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ['product', 'created_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'created_at']
    search_fields = ['user__username']
    inlines = [WishlistItemInline]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'product', 'created_at']
    search_fields = ['wishlist__user__username', 'product__name']
