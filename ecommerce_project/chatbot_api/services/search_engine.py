import re
from decimal import Decimal

from django.db.models import Q

from products.models import Product

USE_CASE_KEYWORDS = {
    'programming': ['programming', 'coding', 'developer', 'software', 'code', 'program', 'development'],
    'gaming': ['gaming', 'game', 'games', 'gamer'],
    'college': ['college', 'student', 'university', 'school', 'study'],
    'video_editing': ['video editing', 'editing', 'render', 'rendering', 'creative', 'content creation'],
    'lightweight': ['lightweight', 'portable', 'thin', 'light', 'ultrabook', 'travel'],
    'budget': ['cheap', 'cheapest', 'budget', 'affordable', 'inexpensive', 'economical', 'low cost'],
    'premium': ['premium', 'high-end', 'luxury', 'best', 'top', 'pro'],
    'business': ['business', 'office', 'professional', 'work', 'productivity'],
}

PRICE_PATTERNS = [
    (r'under\s*\$?(\d+)', 'max'),
    (r'below\s*\$?(\d+)', 'max'),
    (r'less than\s*\$?(\d+)', 'max'),
    (r'\$?(\d+)\s*and\s*under', 'max'),
    (r'up to\s*\$?(\d+)', 'max'),
    (r'max\s*\$?(\d+)', 'max'),
    (r'over\s*\$?(\d+)', 'min'),
    (r'above\s*\$?(\d+)', 'min'),
    (r'more than\s*\$?(\d+)', 'min'),
    (r'min\s*\$?(\d+)', 'min'),
    (r'\$?(\d+)\s*-\s*\$?(\d+)', 'range'),
    (r'between\s*\$?(\d+)\s*and\s*\$?(\d+)', 'range'),
    (r'\$(\d+)', 'exact'),
]


def extract_use_case(message):
    msg = message.lower()
    for use_case, keywords in USE_CASE_KEYWORDS.items():
        for kw in keywords:
            if kw in msg:
                return use_case
    return None


def extract_price_range(message):
    msg = message.lower()
    for pattern, ptype in PRICE_PATTERNS:
        match = re.search(pattern, msg)
        if match:
            if ptype == 'max':
                return None, Decimal(match.group(1))
            elif ptype == 'min':
                return Decimal(match.group(1)), None
            elif ptype == 'range':
                return Decimal(match.group(1)), Decimal(match.group(2))
            elif ptype == 'exact':
                val = Decimal(match.group(1))
                return val - val * Decimal('0.1'), val + val * Decimal('0.1')
    return None, None


def extract_category(message):
    categories = list(Product.objects.values_list('category__name', flat=True).distinct())
    msg = message.lower()
    for cat in categories:
        if cat.lower() in msg:
            return cat
    return None


def extract_brand(message):
    brands = list(Product.objects.values_list('brand__name', flat=True).distinct())
    msg = message.lower()
    for brand in brands:
        if brand and brand.lower() in msg:
            return brand
    return None


def extract_search_terms(message):
    stopwords = {
        'a', 'an', 'the', 'for', 'and', 'or', 'in', 'of', 'to', 'is', 'on', 'at',
        'with', 'i', 'me', 'my', 'we', 'our', 'you', 'your', 'it', 'its',
        'want', 'need', 'looking', 'show', 'find', 'get', 'some', 'please',
        'can', 'could', 'would', 'should', 'do', 'does', 'did', 'has', 'have',
        'tell', 'give', 'recommend', 'suggest', 'compare',
    }
    msg = message.lower()
    for pattern, _ in PRICE_PATTERNS:
        msg = re.sub(pattern, '', msg, flags=re.IGNORECASE)
    for keywords in USE_CASE_KEYWORDS.values():
        for kw in keywords:
            msg = msg.replace(kw, '')
    tokens = msg.split()
    meaningful = [t for t in tokens if t not in stopwords and len(t) > 1]
    return ' '.join(meaningful)


def search_with_intent(message):
    use_case = extract_use_case(message)
    min_price, max_price = extract_price_range(message)
    category_name = extract_category(message)
    brand_name = extract_brand(message)
    search_terms = extract_search_terms(message)

    q = Q(is_active=True, stock__gt=0)

    if category_name:
        q &= Q(category__name__icontains=category_name)
    if brand_name:
        q &= Q(brand__name__icontains=brand_name)

    if max_price is not None:
        q &= (Q(price__lte=max_price) | Q(discount_price__lte=max_price))
    if min_price is not None:
        q &= (Q(price__gte=min_price) | Q(discount_price__gte=min_price))

    if search_terms.strip():
        word_q = Q()
        for word in search_terms.split():
            word_q |= (
                Q(name__icontains=word) |
                Q(description__icontains=word) |
                Q(category__name__icontains=word) |
                Q(brand__name__icontains=word)
            )
        q &= word_q

    results = list(
        Product.objects.filter(q)
        .select_related('category', 'brand')
        .distinct()[:20]
    )

    if not results and search_terms.strip():
        broader_q = Q(is_active=True, stock__gt=0)
        for word in search_terms.split():
            broader_q |= Q(name__icontains=word)
        results = list(
            Product.objects.filter(broader_q)
            .select_related('category', 'brand')
            .distinct()[:10]
        )

    return results, {
        'use_case': use_case,
        'category': category_name,
        'brand': brand_name,
        'min_price': float(min_price) if min_price else None,
        'max_price': float(max_price) if max_price else None,
    }


def search_suggestions(query, limit=5):
    if not query or len(query) < 2:
        return []
    results = list(
        Product.objects.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query),
            is_active=True,
        )
        .select_related('category', 'brand')
        .distinct()[:limit]
    )
    suggestions = []
    for p in results:
        price = p.discount_price if p.is_on_sale else p.price
        suggestions.append({
            'id': p.id,
            'name': p.name,
            'brand': p.brand.name if p.brand else 'N/A',
            'category': p.category.name,
            'price': float(price),
            'slug': p.slug,
        })
    return suggestions
