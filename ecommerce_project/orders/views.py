from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, FormView, TemplateView, View

from accounts.models import Address, PaymentMethod
from cart import utils as cart_utils
from dashboard.models import Notification
from products.models import Product

from .forms import CheckoutForm
from .models import Order, OrderItem


class CheckoutView(LoginRequiredMixin, FormView):
    template_name = 'orders/checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy('orders:order_complete')

    def dispatch(self, request, *args, **kwargs):
        if cart_utils.get_total_items(request) == 0:
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart:cart_detail')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        user = self.request.user
        default_address = Address.objects.filter(user=user, is_default=True).first()
        if default_address:
            return {'address_id': default_address}
        address = Address.objects.filter(user=user).first()
        if address:
            return {'address_id': address}
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_items'] = cart_utils.get_items(self.request)
        context['total_price'] = cart_utils.get_total_price(self.request)
        context['total_items'] = cart_utils.get_total_items(self.request)
        context['saved_addresses'] = Address.objects.filter(user=self.request.user)
        context['payment_methods'] = PaymentMethod.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        user = self.request.user
        cart_items = cart_utils.get_items(self.request)

        for item in cart_items:
            if item['product'].stock < item['quantity']:
                form.add_error(
                    None,
                    f"Insufficient stock for '{item['product'].name}'. "
                    f"Available: {item['product'].stock}, requested: {item['quantity']}.",
                )
                return self.form_invalid(form)

        payment_method = form.cleaned_data['payment_method_id']
        addr = form.cleaned_data['address_id']

        if not addr:
            addr = Address(
                user=user,
                full_name=form.cleaned_data['full_name'],
                phone_number=form.cleaned_data['phone_number'],
                address_line_1=form.cleaned_data['address_line_1'],
                city=form.cleaned_data['city'],
                province_or_state=form.cleaned_data['province_or_state'],
                postal_code=form.cleaned_data['postal_code'],
                country=form.cleaned_data['country'],
            )
            if form.cleaned_data.get('save_address'):
                if not Address.objects.filter(user=user).exists():
                    addr.is_default = True
                addr.save()

        with transaction.atomic():
            shipping_text = (
                f'{addr.full_name}\n'
                f'{addr.phone_number}\n'
                f'{addr.address_line_1}\n'
                f'{addr.city}, {addr.province_or_state} {addr.postal_code}\n'
                f'{addr.country}'
            )

            name_parts = addr.full_name.split(maxsplit=1)
            order = Order.objects.create(
                user=user,
                total_amount=sum(item['total_price'] for item in cart_items),
                status=Order.Status.PENDING,
                phone_number=addr.phone_number,
                shipping_address=shipping_text,
                payment_method=payment_method,
                payment_status=Order.PaymentStatus.PENDING,
                first_name=name_parts[0],
                last_name=name_parts[1] if len(name_parts) > 1 else '',
                email=user.email,
                address=addr.address_line_1,
                city=addr.city,
                postal_code=addr.postal_code,
                country=addr.country,
            )

            for item in cart_items:
                product = item['product']
                quantity = item['quantity']
                price = item['effective_price']

                affected = Product.objects.filter(
                    id=product.id, stock__gte=quantity
                ).update(stock=F('stock') - quantity)

                if affected == 0:
                    transaction.set_rollback(True)
                    form.add_error(
                        None,
                        f"Insufficient stock for '{product.name}'. "
                        f"Available: {product.stock}, requested: {quantity}.",
                    )
                    return self.form_invalid(form)

                OrderItem.objects.create(
                    order=order, product=product,
                    quantity=quantity, price=price,
                )

            Notification.objects.create(
                title='New Order Received',
                message=(
                    f"Order #{order.order_number} has been placed by "
                    f"{order.first_name} {order.last_name}."
                ),
                related_order=order,
            )

            cart_utils.clear(self.request)

        self.request.session['completed_order_id'] = order.id
        return super().form_valid(form)


class OrderCompleteView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/order_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.session.pop('completed_order_id', None)
        if order_id:
            order = get_object_or_404(
                Order.objects.select_related('payment_method'),
                id=order_id, user=self.request.user,
            )
            context['order'] = order
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).select_related('payment_method').prefetch_related('items__product')


class ConfirmReceivedView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(
            Order, pk=pk, user=request.user, status=Order.Status.SHIPPED
        )
        order.status = Order.Status.DELIVERED
        order.save()

        from dashboard.models import Notification
        Notification.objects.create(
            title='Order Received by Customer',
            message=(
                f"Order #{order.order_number} has been confirmed as received by "
                f"{order.first_name} {order.last_name}."
            ),
            related_order=order,
        )

        messages.success(request, f'Order #{order.order_number} marked as received. Thank you!')
        return redirect(reverse('orders:order_detail', kwargs={'pk': pk}))
