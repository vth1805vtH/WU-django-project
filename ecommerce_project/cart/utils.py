from django.shortcuts import get_object_or_404

from products.models import Product

from .models import Cart, CartItem

SESSION_CART_KEY = 'cart'


def _get_session_cart(request):
    return request.session.get(SESSION_CART_KEY, {})


def _save_session_cart(request, cart_data):
    request.session[SESSION_CART_KEY] = cart_data
    request.session.modified = True


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    return None


def get_total_items(request):
    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        return cart.total_items
    cart_data = _get_session_cart(request)
    return sum(cart_data.values())


def get_total_price(request):
    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        return cart.total_price
    cart_data = _get_session_cart(request)
    total = 0
    for product_id, quantity in cart_data.items():
        product = get_object_or_404(Product, id=int(product_id), is_active=True)
        if product.is_on_sale and product.discount_price is not None:
            price = product.discount_price
        else:
            price = product.price
        total += price * quantity
    return total


def add(request, product_id, quantity=1):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': 0},
        )
        item.quantity = item.quantity + quantity
        item.save()
    else:
        cart_data = _get_session_cart(request)
        product_id_str = str(product_id)
        current = cart_data.get(product_id_str, 0)
        cart_data[product_id_str] = current + quantity
        _save_session_cart(request, cart_data)


def remove(request, product_id):
    if request.user.is_authenticated:
        CartItem.objects.filter(
            cart__user=request.user, product_id=product_id
        ).delete()
    else:
        cart_data = _get_session_cart(request)
        cart_data.pop(str(product_id), None)
        _save_session_cart(request, cart_data)


def update_quantity(request, product_id, quantity):
    if quantity < 1:
        remove(request, product_id)
        return

    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        CartItem.objects.filter(cart=cart, product_id=product_id).update(
            quantity=quantity
        )
    else:
        cart_data = _get_session_cart(request)
        cart_data[str(product_id)] = quantity
        _save_session_cart(request, cart_data)


def get_items(request):
    items = []

    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        for item in cart.items.select_related('product__category').all():
            items.append({
                'product': item.product,
                'quantity': item.quantity,
                'total_price': item.total_price,
                'effective_price': item.effective_price,
            })
    else:
        cart_data = _get_session_cart(request)
        for product_id_str, quantity in cart_data.items():
            product = get_object_or_404(Product, id=int(product_id_str), is_active=True)
            if product.is_on_sale and product.discount_price is not None:
                price = product.discount_price
            else:
                price = product.price
            items.append({
                'product': product,
                'quantity': quantity,
                'total_price': price * quantity,
                'effective_price': price,
            })

    return items


def clear(request):
    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        cart.items.all().delete()
    else:
        _save_session_cart(request, {})
