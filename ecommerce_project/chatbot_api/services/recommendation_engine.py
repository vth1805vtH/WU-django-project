from decimal import Decimal
from django.db.models import Count, Q
from products.models import Product
from products.services.recommendation_service import get_recommendations as get_similar_products
from products.services.recommendation_service import get_recently_viewed


def get_personalized_recommendations(user, limit=5):
    scores = {}
    recently_viewed = get_recently_viewed(user, 10)
    for p in recently_viewed:
        if p.is_active and p.stock > 0:
            scores[p.id] = scores.get(p.id, 0) + 3

    try:
        cart = user.cart
        for item in cart.items.select_related('product').all():
            p = item.product
            if p.is_active and p.stock > 0:
                scores[p.id] = scores.get(p.id, 0) + 4
                related = Product.objects.filter(
                    category=p.category, is_active=True, stock__gt=0
                ).exclude(pk=p.pk)[:3]
                for rp in related:
                    scores[rp.id] = scores.get(rp.id, 0) + 2
    except Exception:
        pass

    orders = user.orders.filter(~Q(status='cancelled'))
    for order in orders:
        for item in order.items.select_related('product').all():
            p = item.product
            if p and p.is_active and p.stock > 0:
                scores[p.id] = scores.get(p.id, 0) + 2

    if not scores:
        return list(
            Product.objects.filter(is_active=True, stock__gt=0)
            .order_by('-created_at')[:limit]
        )

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    pks = [pk for pk, _ in ranked[:limit * 2]]
    preserved = {pk: i for i, pk in enumerate(pks)}
    results = list(Product.objects.filter(pk__in=pks, is_active=True, stock__gt=0))
    results.sort(key=lambda p: preserved.get(p.id, float('inf')))
    return results[:limit]


def get_recommendations_by_needs(category_name=None, brand_name=None, max_price=None, min_price=None, limit=5):
    q = Q(is_active=True, stock__gt=0)
    if category_name:
        q &= Q(category__name__icontains=category_name)
    if brand_name:
        q &= Q(brand__name__icontains=brand_name)
    if max_price is not None:
        q &= (Q(price__lte=max_price) | Q(discount_price__lte=max_price))
    if min_price is not None:
        q &= (Q(price__gte=min_price) | Q(discount_price__gte=min_price))
    return list(Product.objects.filter(q).select_related('category', 'brand')[:limit])


def get_deals(limit=5):
    return list(
        Product.objects.filter(is_active=True, stock__gt=0, discount_price__isnull=False)
        .exclude(discount_price=0)
        .select_related('category', 'brand')
        .order_by('?')[:limit]
    )


def get_new_arrivals(limit=5):
    return list(
        Product.objects.filter(is_active=True, stock__gt=0)
        .select_related('category', 'brand')
        .order_by('-created_at')[:limit]
    )


def get_best_sellers(limit=5):
    from orders.models import OrderItem
    popular = (
        OrderItem.objects
        .values('product_id')
        .annotate(total_sold=Count('id'))
        .filter(product__is_active=True)
        .order_by('-total_sold')[:limit]
    )
    pks = [item['product_id'] for item in popular]
    if not pks:
        return get_new_arrivals(limit)
    preserved = {pk: i for i, pk in enumerate(pks)}
    results = list(Product.objects.filter(pk__in=pks, is_active=True, stock__gt=0))
    results.sort(key=lambda p: preserved.get(p.id, float('inf')))
    return results[:limit]


def compare_products(product_ids):
    products = list(
        Product.objects.filter(pk__in=product_ids, is_active=True)
        .select_related('category', 'brand')
    )
    if len(products) < 2:
        return None
    comparison = []
    for p in products:
        price = p.discount_price if p.is_on_sale else p.price
        entry = {
            'id': p.id,
            'name': p.name,
            'brand': p.brand.name if p.brand else 'N/A',
            'category': p.category.name,
            'price': float(price),
            'original_price': float(p.price) if p.is_on_sale else None,
            'discount': f'{p.discount_percentage}%' if p.is_on_sale else None,
            'rating': float(p.average_rating) if p.average_rating > 0 else None,
            'reviews': p.review_count,
            'stock': p.stock,
            'description': p.description[:200] if p.description else '',
        }
        strengths = _generate_strengths(p)
        weaknesses = _generate_weaknesses(p)
        entry['strengths'] = strengths
        entry['weaknesses'] = weaknesses
        comparison.append(entry)
    return comparison


def _generate_strengths(product):
    strengths = []
    price = product.discount_price if product.is_on_sale else product.price
    if product.discount_percentage > 0:
        strengths.append(f"Great value — {product.discount_percentage}% off")
    if product.average_rating >= 4:
        strengths.append(f"Highly rated ({product.average_rating}/5)")
    if product.stock > 50:
        strengths.append("Well-stocked, readily available")
    if price < 500:
        strengths.append("Budget-friendly price point")
    elif price > 2000:
        strengths.append("Premium quality product")
    if product.review_count > 10:
        strengths.append(f"Trusted by {product.review_count} reviewers")
    if product.description and ('lightweight' in product.description.lower() or 'portable' in product.description.lower()):
        strengths.append("Lightweight and portable design")
    if product.description and ('long battery' in product.description.lower() or 'battery life' in product.description.lower()):
        strengths.append("Long battery life")
    if product.description and ('powerful' in product.description.lower() or 'high-performance' in product.description.lower()):
        strengths.append("High performance")
    if not strengths:
        strengths.append("Solid all-around product")
    return strengths


def _generate_weaknesses(product):
    weaknesses = []
    price = product.discount_price if product.is_on_sale else product.price
    if product.average_rating > 0 and product.average_rating < 3.5:
        weaknesses.append("Below-average customer ratings")
    if product.stock < 5:
        weaknesses.append("Limited stock available")
    if price > 2000:
        weaknesses.append("Premium price point")
    if product.discount_percentage == 0 and price > 1000:
        weaknesses.append("No current discount available")
    if product.review_count == 0:
        weaknesses.append("No customer reviews yet")
    if price < 200:
        weaknesses.append("Budget build may compromise durability")
    product.description.lower()
    if not weaknesses:
        weaknesses.append("None significant")
    return weaknesses


def generate_reason(product, user_context=None):
    price = product.discount_price if product.is_on_sale else product.price
    parts = []
    if user_context == 'programming' or user_context == 'coding':
        parts.append("Strong performance for development tasks")
    elif user_context == 'gaming':
        parts.append("Excellent gaming performance")
    elif user_context == 'college' or user_context == 'student':
        parts.append("Great balance of portability and performance for students")
    elif user_context == 'video editing':
        parts.append("Handles video editing workloads efficiently")
    elif user_context == 'lightweight':
        parts.append("Ultra-portable design for on-the-go use")
    elif user_context == 'budget':
        parts.append(f"Excellent value at {format_price(price)}")
    else:
        if product.average_rating >= 4:
            parts.append(f"Top-rated with {product.average_rating}/5 stars")
        if product.discount_percentage > 0:
            parts.append(f"Save {product.discount_percentage}% — great deal")
        else:
            parts.append("Reliable choice with solid features")
    if product.brand:
        parts.append(f"Trusted {product.brand.name} quality")
    return '. '.join(parts) + '.'


def format_price(amount):
    return f'${amount:.2f}' if isinstance(amount, Decimal) else f'${float(amount):.2f}'


def format_recommendations(products, context=None, title='Recommended Products'):
    if not products:
        return "I couldn't find any products matching your needs right now."
    lines = [title + ':']
    lines.append('')
    for p in products:
        reason = generate_reason(p, context)
        price = p.discount_price if p.is_on_sale else p.price
        sale = f' (Was {format_price(p.price)}, save {p.discount_percentage}%)' if p.is_on_sale else ''
        lines.append(f'  {p.name}')
        lines.append(f'  Price: {format_price(price)}{sale}')
        lines.append(f'  Reason: {reason}')
        lines.append('')
    return '\n'.join(lines).strip()


def format_comparison(comparison):
    if not comparison or len(comparison) < 2:
        return "I need at least two products to compare."
    lines = ['Product Comparison:']
    lines.append('')
    headers = ['Feature'] + [c['name'][:20] for c in comparison]
    sep = '  ' + '-' * 60
    lines.append(sep)
    rows = [
        ('Brand', 'brand'),
        ('Category', 'category'),
        ('Price', 'price_formatted'),
        ('Discount', 'discount_display'),
        ('Rating', 'rating_display'),
        ('Reviews', 'reviews'),
        ('Stock', 'stock'),
    ]
    for label, key in rows:
        row = [f'  {label:<12}']
        for c in comparison:
            if key == 'price_formatted':
                val = format_price(Decimal(str(c['price'])))
                if c['original_price']:
                    val += f' (was {format_price(Decimal(str(c["original_price"])))})'
            elif key == 'discount_display':
                val = c['discount'] or 'None'
            elif key == 'rating_display':
                val = f'{c["rating"]}/5' if c['rating'] else 'N/A'
            else:
                val = str(c.get(key, ''))
            row.append(f'{val:<20}')
        lines.append('  '.join(row))
    lines.append(sep)
    lines.append('')
    lines.append('  Strengths & Weaknesses:')
    lines.append('')
    for c in comparison:
        lines.append(f'  {c["name"]}:')
        lines.append(f'    Strengths: {", ".join(c["strengths"][:3])}')
        lines.append(f'    Weaknesses: {", ".join(c["weaknesses"][:2])}')
        lines.append('')
    return '\n'.join(lines).strip()
