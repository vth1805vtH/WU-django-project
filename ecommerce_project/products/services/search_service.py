from django.db.models import Q

from products.models import Product


def _keyword_search(query):
    words = query.split()
    q = Q()
    for word in words:
        stopwords = {'a', 'an', 'the', 'for', 'and', 'or', 'in', 'of', 'to', 'is', 'on', 'at', 'with', 'best', 'cheap', 'lightweight', 'top', 'good', 'great', 'nice', 'new'}
        if word.lower() in stopwords:
            continue
        word_filter = (
            Q(name__icontains=word) |
            Q(description__icontains=word) |
            Q(category__name__icontains=word) |
            Q(brand__name__icontains=word)
        )
        q |= word_filter
    return q


def _score_product(product, score_keywords):
    score = 0
    text = (
        product.name.lower() + ' ' +
        product.description.lower() + ' ' +
        product.category.name.lower() + ' ' +
        (product.brand.name.lower() if product.brand else '')
    )

    for kw in score_keywords:
        kw = kw.lower()
        if kw in text:
            if kw in product.name.lower():
                score += 4
            elif product.brand and kw in product.brand.name.lower():
                score += 3
            elif kw in product.category.name.lower():
                score += 3
            elif kw in product.description.lower():
                score += 2
            else:
                score += 1

    return score


def smart_search(query):
    if not query or not query.strip():
        return Product.objects.filter(is_active=True).none()

    q = _keyword_search(query.strip())
    products = list(
        Product.objects.filter(q, is_active=True)
        .select_related('category', 'brand')
        .distinct()[:20]
    )

    score_terms = query.lower().split()
    products.sort(key=lambda p: _score_product(p, score_terms), reverse=True)
    return products
