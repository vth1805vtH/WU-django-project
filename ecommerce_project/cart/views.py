from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from . import utils


class CartDetailView(TemplateView):
    template_name = 'cart/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_items'] = utils.get_items(self.request)
        context['total_price'] = utils.get_total_price(self.request)
        context['total_items'] = utils.get_total_items(self.request)
        return context


@require_POST
def cart_add(request, product_id):
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
    utils.add(request, product_id, quantity)
    messages.success(request, 'Item added to cart.')
    return redirect(request.META.get('HTTP_REFERER', reverse('products:product_list')))


@require_POST
def cart_remove(request, product_id):
    utils.remove(request, product_id)
    messages.success(request, 'Item removed from cart.')
    return redirect('cart:cart_detail')


@require_POST
def cart_update(request, product_id):
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
    utils.update_quantity(request, product_id, quantity)
    messages.success(request, 'Cart updated.')
    return redirect('cart:cart_detail')
