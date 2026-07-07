from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from products.models import Product

from .models import Wishlist, WishlistItem


class WishlistListView(LoginRequiredMixin, ListView):
    template_name = 'wishlist/wishlist_list.html'
    context_object_name = 'wishlist_items'

    def get_queryset(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist.items.select_related('product__category').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        context['wishlist'] = wishlist
        return context


@login_required
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    messages.success(request, f'"{product.name}" added to your wishlist.')
    return redirect(request.META.get('HTTP_REFERER', reverse('products:product_list')))


@login_required
@require_POST
def wishlist_remove(request, product_id):
    WishlistItem.objects.filter(
        wishlist__user=request.user, product_id=product_id
    ).delete()
    messages.success(request, 'Item removed from wishlist.')
    return redirect('wishlist:wishlist_list')
