from datetime import timedelta

from django.db.models import Count, DecimalField, F, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from orders.models import Order, OrderItem
from products.models import Product

REVENUE_STATUSES = [Order.Status.APPROVED, Order.Status.PROCESSING,
                    Order.Status.SHIPPED, Order.Status.DELIVERED]


def get_best_selling_products(limit=5):
    return list(
        OrderItem.objects
        .filter(order__status__in=REVENUE_STATUSES)
        .values('product_id', 'product__name', 'product__image')
        .annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'), output_field=DecimalField()),
        )
        .order_by('-total_quantity')[:limit]
    )


def get_top_brands(limit=5):
    return list(
        OrderItem.objects
        .filter(
            order__status__in=REVENUE_STATUSES,
            product__brand__isnull=False,
        )
        .values('product__brand__name', 'product__brand__slug')
        .annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'), output_field=DecimalField()),
        )
        .order_by('-total_revenue')[:limit]
    )


def get_revenue_trends(months=6):
    cutoff = timezone.now() - timedelta(days=30 * months)
    return list(
        Order.objects
        .filter(created_at__gte=cutoff, status__in=REVENUE_STATUSES)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(revenue=Sum('total_amount'), order_count=Count('id'))
        .order_by('month')
    )


def get_order_growth(months=6):
    cutoff = timezone.now() - timedelta(days=30 * months)
    return list(
        Order.objects
        .filter(created_at__gte=cutoff)
        .exclude(status=Order.Status.CANCELLED)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )


def get_low_stock_alerts(threshold=5):
    return list(
        Product.objects
        .filter(is_active=True, stock__lt=threshold)
        .order_by('stock')
        .values('name', 'stock', 'brand__name')
    )


def get_insights():
    best_sellers = get_best_selling_products(5)
    low_stock = get_low_stock_alerts(5)
    insights = []

    if best_sellers:
        top = best_sellers[0]
        insights.append(
            f'Best-selling product is {top["product__name"]} '
            f'with {top["total_quantity"]} units sold.'
        )

    if low_stock:
        count = len(low_stock)
        insights.append(
            f'{count} product{"s" if count > 1 else ""} {"are" if count > 1 else "is"} '
            f'low on stock and need restocking.'
        )

    if not insights:
        insights.append('No significant trends to report yet.')

    return insights


def get_full_analytics():
    return {
        'best_sellers': get_best_selling_products(),
        'top_brands': get_top_brands(),
        'revenue_trends': get_revenue_trends(),
        'order_growth': get_order_growth(),
        'low_stock': get_low_stock_alerts(),
        'insights': get_insights(),
    }
