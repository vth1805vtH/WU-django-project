import re
from decimal import Decimal

from . import recommendation_engine as rec
from . import search_engine as search
from . import order_assistant as order_asm

# --- Intent Patterns ---

GREETINGS = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "yo", "howdy", "sup"}
THANK_YOU = {"thanks", "thank you", "thx", "ty", "appreciate it", "thanks a lot"}
EXIT_WORDS = {"bye", "goodbye", "see you", "cya", "exit", "quit", "see ya"}

COMPARE_PATTERNS = [
    re.compile(r'compare\s+(.+?)\s+(?:and|vs\.?|versus|with)\s+(.+)', re.IGNORECASE),
    re.compile(r'difference\s+(?:between\s+)?(.+?)\s+(?:and|vs\.?|versus)\s+(.+)', re.IGNORECASE),
    re.compile(r'which\s+(?:is\s+)?better\s+(.+?)\s+(?:or|and)\s+(.+)', re.IGNORECASE),
]

ORDER_PATTERNS = [
    re.compile(r'(?:track|where\s+is|status\s+of|check)\s+(?:my\s+)?order\s*#?(\w+)', re.IGNORECASE),
    re.compile(r'(?:my\s+)?orders?', re.IGNORECASE),
    re.compile(r'(?:latest|recent|last)\s+order', re.IGNORECASE),
]

ADDRESS_PATTERNS = [
    re.compile(r'(?:my\s+)?(?:default|saved|delivery|shipping)?\s*address(?:es)?', re.IGNORECASE),
    re.compile(r'where\s+(?:will\s+)?(?:my\s+)?order\s+(?:be\s+)?(?:shipped|delivered)', re.IGNORECASE),
    re.compile(r'add\s+(?:a\s+)?(?:new\s+)?(?:delivery|shipping)?\s*address', re.IGNORECASE),
]

PAYMENT_PATTERNS = [
    re.compile(r'(?:how\s+to\s+)?pay\s+(?:with|using)\s+(.+)', re.IGNORECASE),
    re.compile(r'(?:payment|pay)\s*(?:methods?|options?)', re.IGNORECASE),
    re.compile(r'(?:how|process|make)\s+(?:to\s+)?(?:pay|payment)', re.IGNORECASE),
]

INFO_PATTERNS = {
    'shipping': re.compile(r'(?:shipping|delivery|ship|track)', re.IGNORECASE),
    'return': re.compile(r'(?:return|refund|exchange)', re.IGNORECASE),
    'warranty': re.compile(r'(?:warranty|guarantee)', re.IGNORECASE),
}

DEALS_PATTERNS = re.compile(r'(?:deal|discount|sale|offer|cheap|budget|promotion)', re.IGNORECASE)
NEW_ARRIVALS_PATTERNS = re.compile(r'(?:new|arrival|latest|just\s+(?:in|arrived))', re.IGNORECASE)
BEST_SELLERS_PATTERNS = re.compile(r'(?:best.?seller|popular|top.?rated|most\s+(?:popular|sold))', re.IGNORECASE)
RECOMMEND_PATTERNS = re.compile(r'(?:recommend|suggest|what\s+(?:should|do\s+you)|give\s+me)', re.IGNORECASE)
INSIGHTS_PATTERNS = re.compile(r'(?:insight|analytics|report|revenue|sales\s*(?:data|trend)|best.?selling)', re.IGNORECASE)

WELCOME_MESSAGE = """Welcome to ShopEase! I'm your AI shopping assistant.

I can help you with:
  1. Product recommendations — "recommend a laptop for programming"
  2. Compare products — "compare ASUS ROG and Lenovo Legion"
  3. Track orders — "where is my order?"
  4. Deals & discounts — "show me deals under $1000"
  5. Payment info — "how to pay with ABA?"
  6. Personalized picks — based on your browsing & purchases
  7. Store insights (staff) — sales reports & analytics

How can I help you today?"""


def is_greeting(message):
    m = message.lower().strip().rstrip('!.,')
    return m in GREETINGS


def is_thanks(message):
    return message.lower().strip() in THANK_YOU


def is_exit(message):
    return message.lower().strip() in EXIT_WORDS


def find_compare_products(message):
    for pattern in COMPARE_PATTERNS:
        match = pattern.search(message)
        if match:
            groups = match.groups()
            name1 = groups[0].strip()
            name2 = groups[1].strip()
            return name1, name2
    return None, None


def find_order_ref(message):
    for pattern in ORDER_PATTERNS:
        match = pattern.search(message)
        if match:
            if match.lastindex and match.group(1):
                return match.group(1)
            return True
    return None


def _format_price(amount):
    return f'${amount:.2f}' if isinstance(amount, Decimal) else f'${float(amount):.2f}'


def process_message(user, message, history=None):
    msg = message.strip()
    if not msg:
        return "Please ask me something! I'm here to help."

    if is_greeting(msg):
        return WELCOME_MESSAGE

    if is_thanks(msg):
        return "You're welcome! Let me know if you need anything else — I'm always here to help."

    if is_exit(msg):
        return "Thanks for visiting ShopEase! Have a great day!"

    # --- Compare Products ---
    name1, name2 = find_compare_products(msg)
    if name1 and name2:
        p1 = _find_product_by_name(name1)
        p2 = _find_product_by_name(name2)
        if p1 and p2:
            comparison = rec.compare_products([p1.id, p2.id])
            if comparison:
                return rec.format_comparison(comparison)
            return "I found both products but couldn't generate a comparison."
        found = []
        if p1:
            found.append(name1)
        if p2:
            found.append(name2)
        if found:
            return f"I found {', '.join(found)} but couldn't find the other product(s). Please check the product names."
        return "I couldn't find those products. Try checking the exact product names."

    # --- Order Tracking ---
    order_ref = find_order_ref(msg)
    if order_ref is not None and user.is_authenticated:
        if isinstance(order_ref, str) and order_ref is not True:
            order = order_asm.get_order_by_number(user, order_ref.upper())
            if order:
                return order_asm.format_order_detail(order)
            return f"I couldn't find an order with number '{order_ref}'. Please check your order number."
        orders = order_asm.get_user_orders(user)
        if orders:
            if len(orders) == 1:
                return order_asm.format_order_detail(orders[0])
            return order_asm.format_orders(orders)
        return "You don't have any orders yet. Would you like to browse our products?"

    # --- Address ---
    if any(p.search(msg) for p in ADDRESS_PATTERNS):
        if not user.is_authenticated:
            return "Please log in to manage your addresses. You can also add a new address during checkout."
        if 'add' in msg.lower() or 'new' in msg.lower():
            return "You can add a new delivery address from your account settings or during checkout. Would you like to go to your address settings?"
        if 'default' in msg.lower():
            addr = order_asm.get_default_address(user)
            return order_asm.format_default_address(addr)
        addresses = order_asm.get_addresses(user)
        return order_asm.format_addresses(addresses)

    # --- Payment Methods ---
    for pattern in PAYMENT_PATTERNS:
        match = pattern.search(msg)
        if match:
            if match.lastindex and match.group(1):
                bank_name = match.group(1).strip()
                response = order_asm.get_info_response(bank_name)
                if response:
                    return response
            methods = order_asm.get_payment_methods()
            return order_asm.format_payment_methods(methods)

    # --- Shipping / Returns / Warranty Info ---
    for topic, pattern in INFO_PATTERNS.items():
        if pattern.search(msg):
            response = order_asm.get_info_response(topic)
            if response:
                return response

    # --- Admin Insights ---
    if INSIGHTS_PATTERNS.search(msg) and user.is_authenticated and user.is_staff:
        insights = order_asm.format_admin_insights(user)
        if insights:
            return insights

    # --- Deals / Discounts ---
    if DEALS_PATTERNS.search(msg):
        max_price = search.extract_price_range(msg)[1]
        if max_price:
            products = search.get_recommendations_by_needs(max_price=max_price, limit=5)
            if products:
                return rec.format_recommendations(products, context='budget', title=f'Deals Under {_format_price(max_price)}')
        products = rec.get_deals(5)
        if products:
            return rec.format_recommendations(products, title='Current Deals')
        return "I don't see any current deals. Check back soon!"

    # --- Best Sellers ---
    if BEST_SELLERS_PATTERNS.search(msg):
        products = rec.get_best_sellers(5)
        if products:
            return rec.format_recommendations(products, title='Best Sellers')
        return "I couldn't fetch best sellers right now. Try asking for recommendations."

    # --- New Arrivals ---
    if NEW_ARRIVALS_PATTERNS.search(msg):
        products = rec.get_new_arrivals(5)
        if products:
            return rec.format_recommendations(products, title='New Arrivals')
        return "No new arrivals at the moment. Check back soon!"

    # --- Product Search / Recommendations ---
    products, intent_data = search.search_with_intent(msg)
    use_case = intent_data['use_case']

    if products:
        title = 'Recommended Products'
        if intent_data['category']:
            title = f'{intent_data["category"]} Recommendations'
        elif use_case:
            title = f'Best {use_case.replace("_", " ").title()} Options'
        return rec.format_recommendations(products, context=use_case, title=title)

    # --- Personalized Recommendations (authenticated users with history) ---
    if user.is_authenticated:
        products = rec.get_personalized_recommendations(user, 5)
        if products:
            return rec.format_recommendations(products, title='Recommended for You')

    # --- Fallback: Suggest help ---
    return WELCOME_MESSAGE


def _find_product_by_name(name):
    from products.models import Product
    name = name.strip()
    product = Product.objects.filter(
        name__icontains=name, is_active=True
    ).first()
    if not product:
        product = Product.objects.filter(
            brand__name__icontains=name, is_active=True
        ).first()
    return product


SUGGESTED_QUESTIONS = [
    "Recommend a laptop for programming",
    "Show products under $1000",
    "Compare two products",
    "Where is my order?",
    "Current deals and discounts",
    "How to pay with ABA?",
    "Best selling products",
    "New arrivals",
]
