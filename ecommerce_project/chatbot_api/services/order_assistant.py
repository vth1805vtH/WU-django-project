from accounts.models import Address, PaymentMethod
from orders.models import Order


def get_user_orders(user, limit=5):
    return list(
        Order.objects.filter(user=user)
        .select_related('payment_method')
        .prefetch_related('items__product')
        .order_by('-created_at')[:limit]
    )


def get_order_by_number(user, order_number):
    try:
        return Order.objects.get(user=user, order_number=order_number)
    except Order.DoesNotExist:
        return None


def get_latest_order(user):
    return Order.objects.filter(user=user).order_by('-created_at').first()


def get_default_address(user):
    try:
        return Address.objects.get(user=user, is_default=True)
    except Address.DoesNotExist:
        return None


def get_addresses(user):
    return list(Address.objects.filter(user=user).order_by('-is_default', '-created_at'))


def get_payment_methods():
    return list(PaymentMethod.objects.filter(is_active=True))


def format_orders(orders):
    if not orders:
        return "You don't have any orders yet. Browse our products and place your first order!"
    lines = ['Your Orders:']
    lines.append('')
    for order in orders:
        lines.append(f'  [Order #{order.order_number}]')
        lines.append(f'     Status: {order.status.title()}')
        lines.append(f'     Total: ${order.total_amount:.2f}')
        lines.append(f'     Payment: {order.payment_status.title()}')
        lines.append(f'     Items: {order.item_count}')
        lines.append(f'     Date: {order.created_at.strftime("%b %d, %Y")}')
        lines.append('')
    return '\n'.join(lines).strip()


def format_order_detail(order):
    lines = [f'Order #{order.order_number}']
    lines.append(f'{"─" * 36}')
    lines.append(f'  Status  : {order.status.title()}')
    lines.append(f'  Total   : ${order.total_amount:.2f}')
    lines.append(f'  Payment : {order.payment_status.title()}')
    if order.payment_method:
        lines.append(f'  Method  : {order.payment_method.name}')
    lines.append(f'  Items   : {order.item_count}')
    lines.append(f'  Date    : {order.created_at.strftime("%b %d, %Y")}')
    lines.append('')
    if order.items.exists():
        lines.append('  Items:')
        for item in order.items.all():
            pname = item.product.name if item.product else 'Unknown'
            lines.append(f'    - {pname} x {item.quantity} — ${item.total_price:.2f}')
    lines.append('')
    if order.status.lower() in ('shipped', 'delivered'):
        lines.append('  Estimated Delivery: Within 2-5 business days')
    elif order.status.lower() == 'processing':
        lines.append('  Your order is being prepared for shipping.')
    elif order.status.lower() == 'pending':
        lines.append('  Your order is awaiting approval.')
    return '\n'.join(lines).strip()


def format_addresses(addresses):
    if not addresses:
        return "You don't have any saved addresses. You can add one from your account settings."
    lines = ['Saved Addresses:']
    lines.append('')
    for addr in addresses:
        default_tag = ' [Default]' if addr.is_default else ''
        lines.append(f'  - {addr.full_name}{default_tag}')
        lines.append(f'    {addr.address_line_1}')
        if addr.address_line_2:
            lines.append(f'    {addr.address_line_2}')
        lines.append(f'    {addr.city}, {addr.province_or_state} {addr.postal_code}')
        lines.append(f'    {addr.country}')
        lines.append(f'    Phone: {addr.phone_number}')
        lines.append('')
    return '\n'.join(lines).strip()


def format_default_address(address):
    if not address:
        return "You don't have a default address set. You can add one in your account settings."
    lines = ['Default Delivery Address:']
    lines.append('')
    lines.append(f'  {address.full_name}')
    lines.append(f'  {address.address_line_1}')
    if address.address_line_2:
        lines.append(f'  {address.address_line_2}')
    lines.append(f'  {address.city}, {address.province_or_state} {address.postal_code}')
    lines.append(f'  {address.country}')
    lines.append(f'  Phone: {address.phone_number}')
    return '\n'.join(lines).strip()


def format_payment_methods(methods):
    if not methods:
        return "We accept various payment methods. Please visit our Help page for details."
    lines = ['Available Payment Methods:']
    lines.append('')
    for m in methods:
        lines.append(f'  - {m.name}')
        if m.description:
            lines.append(f'    {m.description[:150]}')
        lines.append('')
    lines.append('To use a payment method, proceed to checkout and select your preferred option.')
    return '\n'.join(lines).strip()


PAYMENT_INFO = {
    'aba': (
        "To pay with ABA Bank:\n"
        "  1. Open your ABA Mobile app\n"
        "  2. Select 'Scan to Pay' or 'Transfer'\n"
        "  3. Scan our QR code or enter our account number\n"
        "  4. Enter the exact amount\n"
        "  5. Complete the payment\n"
        "  6. Upload the screenshot in checkout\n\n"
        "Your order will be processed once payment is confirmed."
    ),
    'acleda': (
        "To pay with ACLEDA Bank:\n"
        "  1. Open your ACLEDA Mobile app\n"
        "  2. Select 'Scan to Pay' or 'Transfer'\n"
        "  3. Scan our QR code shown at checkout\n"
        "  4. Enter the exact amount\n"
        "  5. Complete the transaction\n"
        "  6. Upload the payment screenshot\n\n"
        "We'll verify your payment within 24 hours."
    ),
    'visa': (
        "To pay with Visa/Mastercard:\n"
        "  1. Proceed to checkout\n"
        "  2. Select 'Card Payment'\n"
        "  3. Enter your card details (number, expiry, CVV)\n"
        "  4. Complete the secure payment\n\n"
        "Your payment is processed securely. We accept Visa and Mastercard."
    ),
}

SHIPPING_INFO = (
    "Shipping Information:\n"
    "  • Standard delivery: 3-7 business days\n"
    "  • Express delivery: 1-2 business days\n"
    "  • Free shipping on orders over $100\n"
    "  • We deliver nationwide\n"
    "  • Tracking number provided once shipped"
)

RETURN_POLICY = (
    "Return Policy:\n"
    "  • 30-day return window from delivery\n"
    "  • Items must be unused and in original packaging\n"
    "  • Free returns for defective items\n"
    "  • Refund processed within 5-7 business days\n"
    "  • Contact support to initiate a return"
)

WARRANTY_INFO = (
    "Warranty Information:\n"
    "  • All electronics come with manufacturer warranty\n"
    "  • Standard warranty: 1 year\n"
    "  • Extended warranty available at checkout\n"
    "  • Warranty covers manufacturing defects"
)


def get_info_response(topic):
    topic = topic.lower().strip()
    if topic in ('aba', 'aba bank', 'aba payment'):
        return PAYMENT_INFO['aba']
    if topic in ('acleda', 'acleda bank', 'acleda payment'):
        return PAYMENT_INFO['acleda']
    if topic in ('visa', 'mastercard', 'card', 'credit card'):
        return PAYMENT_INFO['visa']
    if topic in ('payment', 'pay', 'payment methods'):
        methods = get_payment_methods()
        return format_payment_methods(methods)
    if topic in ('shipping', 'delivery', 'ship'):
        return SHIPPING_INFO
    if topic in ('return', 'returns', 'refund'):
        return RETURN_POLICY
    if topic in ('warranty', 'guarantee'):
        return WARRANTY_INFO
    return None


def format_admin_insights(user):
    from django.db.models import Sum, Count
    from orders.models import OrderItem, Order
    from dashboard.services.analytics_service import get_monthly_revenue
    try:
        if not user.is_staff:
            return None
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(status='delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        low_stock = Product.objects.filter(is_active=True, stock__lt=10).count()
        top_brand = (
            OrderItem.objects
            .filter(product__isnull=False, product__brand__isnull=False)
            .values('product__brand__name')
            .annotate(total=Count('id'))
            .order_by('-total')
            .first()
        )
        revenue_data = get_monthly_revenue()
        lines = ['Store Insights:']
        lines.append('')
        lines.append(f'  Total Orders      : {total_orders}')
        lines.append(f'  Total Revenue     : ${total_revenue:,.2f}')
        lines.append(f'  Low Stock Items   : {low_stock}')
        if top_brand:
            share = (top_brand['total'] / total_orders * 100) if total_orders > 0 else 0
            lines.append(f'  Top Brand         : {top_brand["product__brand__name"]} ({share:.0f}% of sales)')
        if revenue_data:
            lines.append(f'  Monthly Revenue   : ${revenue_data.get("total", 0):,.2f}')
        lines.append('')
        lines.append('Use this data to make informed business decisions.')
        return '\n'.join(lines)
    except Exception:
        return None
