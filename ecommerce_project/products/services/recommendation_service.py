from decimal import Decimal

from django.db.models import Q

from products.models import Product


def get_recommendations(product, limit=4):
    if not product or not product.is_active:
        return Product.objects.none()

    same_category = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)

    same_brand = Product.objects.filter(
        brand=product.brand, is_active=True
    ) if product.brand else Product.objects.none()

    half_price = product.price / Decimal('2')
    double_price = product.price * Decimal('2')

    similar_price = Product.objects.filter(
        is_active=True,
        price__gte=half_price,
        price__lte=double_price,
    ).exclude(pk=product.pk)

    scored = {}

    for qs, weight in [(same_category, 3), (same_brand, 2), (similar_price, 1)]:
        for p in qs.only('pk', 'category', 'brand', 'price', 'stock', 'is_active'):
            if p.stock > 0:
                scored[p.pk] = scored.get(p.pk, 0) + weight

    ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
    pks = [pk for pk, _ in ranked[:limit]]

    if not pks:
        return Product.objects.filter(is_active=True).exclude(pk=product.pk)[:limit]

    preserved = {pk: i for i, pk in enumerate(pks)}
    results = list(Product.objects.filter(pk__in=pks, is_active=True))
    results.sort(key=lambda p: preserved.get(p.pk, float('inf')))
    return results[:limit]


def get_recently_viewed(user, limit=10):
    from products.models import RecentlyViewed

    rv = (
        RecentlyViewed.objects
        .filter(user=user)
        .select_related('product')
        .order_by('-viewed_at')[:limit]
    )
    return [r.product for r in rv if r.product.is_active]
