import os
from decimal import Decimal

import requests
from django.db.models import Q
from dotenv import load_dotenv

load_dotenv()

from products.models import Product

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

GREETINGS = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "yo", "howdy"}
THANK_YOU = {"thanks", "thank you", "thx", "ty", "appreciate it"}
EXIT_WORDS = {"bye", "goodbye", "see you", "cya", "exit", "quit"}
HELP_WORDS = {"help", "what can you do", "capabilities", "commands", "options"}


def format_currency(amount):
    return f'${amount:.2f}' if isinstance(amount, Decimal) else f'${float(amount):.2f}'


def is_greeting(message):
    return message.lower().strip() in GREETINGS or message.lower().strip().rstrip("!.,") in GREETINGS


def is_thanks(message):
    return message.lower().strip() in THANK_YOU


def is_exit(message):
    return message.lower().strip() in EXIT_WORDS


def is_help(message):
    return message.lower().strip() in HELP_WORDS or message.lower().strip().startswith("help")


def clean_query(message):
    price_keywords = {"cheap", "cheapest", "affordable", "budget", "cheaper", "inexpensive", "lowest", "discount", "deal"}
    best_keywords = {"best", "top", "recommend", "recommended", "popular", "highest", "rated", "greatest"}

    q = message.lower().strip()
    tokens = q.split()

    intent = {"cheap": False, "best": False}
    meaningful = []

    for t in tokens:
        if t in price_keywords:
            intent["cheap"] = True
        elif t in best_keywords:
            intent["best"] = True
        elif t not in {"a", "an", "the", "for", "me", "please", "want", "need", "looking", "show", "find", "get", "some", "i", "with"}:
            meaningful.append(t)

    return " ".join(meaningful), intent


def search_products(query, intent):
    q = query.lower().strip()
    if not q:
        products = list(
            Product.objects.filter(is_active=True)
            .select_related("category", "brand")
            .order_by("?")[:10]
        )
        if intent["cheap"]:
            products.sort(key=lambda p: p.discount_price if p.is_on_sale else p.price)
        elif intent["best"]:
            products.sort(key=lambda p: p.average_rating, reverse=True)
        return products

    tokens = q.split()
    conditions = Q(is_active=True)
    price_filters = []
    max_price = None

    for i, token in enumerate(tokens):
        if token in ("under", "below", "less", "cheaper", "max") and i + 1 < len(tokens):
            try:
                max_price = Decimal(tokens[i + 1].replace("$", "").replace(",", ""))
                price_filters.append(Q(price__lte=max_price) | Q(discount_price__lte=max_price))
            except Exception:
                pass
        elif token in ("above", "over", "more", "min") and i + 1 < len(tokens):
            try:
                min_price = Decimal(tokens[i + 1].replace("$", "").replace(",", ""))
                price_filters.append(Q(price__gte=min_price) | Q(discount_price__gte=min_price))
            except Exception:
                pass
        elif token.startswith("$"):
            try:
                amount = Decimal(token.replace("$", "").replace(",", ""))
                price_filters.append(Q(price__lte=amount) | Q(discount_price__lte=amount))
            except Exception:
                pass

    for pf in price_filters:
        conditions &= pf

    search_words = [t for t in tokens if t not in
                    {"under", "below", "less", "cheaper", "max", "above", "over", "more", "min", "a", "an", "the",
                     "for", "me", "please", "want", "need", "looking", "show", "find", "get", "some", "i", "with"}]

    if search_words:
        word_conditions = Q()
        for word in search_words:
            word_conditions |= (
                Q(name__icontains=word) |
                Q(description__icontains=word) |
                Q(category__name__icontains=word) |
                Q(brand__name__icontains=word)
            )
        conditions &= word_conditions

    results = list(
        Product.objects.filter(conditions)
        .select_related("category", "brand")
        .distinct()[:20]
    )

    if intent["cheap"]:
        results.sort(key=lambda p: p.discount_price if p.is_on_sale else p.price)
    elif intent["best"]:
        results.sort(key=lambda p: p.average_rating, reverse=True)

    return results


def format_single_product(p):
    price = p.discount_price if p.is_on_sale else p.price
    lines = [f"  {p.name}"]
    lines.append(f"  {'─' * 36}")
    lines.append(f"  Price    : {format_currency(price)}")
    if p.is_on_sale:
        lines.append(f"  Sale     : Was {format_currency(p.price)}, save {p.discount_percentage}%!")
    if p.brand:
        lines.append(f"  Brand    : {p.brand.name}")
    lines.append(f"  Category : {p.category.name}")
    rating = f"{p.average_rating}/5 ({p.review_count} reviews)" if p.average_rating > 0 else "No ratings yet"
    lines.append(f"  Rating   : {rating}")
    lines.append(f"  Stock    : {p.stock} units")
    if p.description:
        desc = p.description[:200] + "..." if len(p.description) > 200 else p.description
        lines.append(f"  Desc     : {desc}")
    return "\n".join(lines)


def format_product_list(products, intent):
    lines = []
    for i, p in enumerate(products[:8], 1):
        price = p.discount_price if p.is_on_sale else p.price
        sale = f" [SAVE {p.discount_percentage}%]" if p.is_on_sale else ""
        lines.append(f"  {i}. {p.name} — {format_currency(price)}{sale}")
    if len(products) > 8:
        lines.append(f"  ... and {len(products) - 8} more")
    return "\n".join(lines)


def format_no_results(query):
    suggestions = list(
        Product.objects.filter(is_active=True)
        .select_related("category", "brand")
        .order_by("?")[:5]
    )
    if suggestions:
        cats = sorted(set(p.category.name for p in suggestions))
        brands = sorted(set(p.brand.name for p in suggestions if p.brand))
        parts = [f'Sorry, no products match "{query}".']
        parts.append(f"Try browsing: {', '.join(cats)}")
        if brands:
            parts.append(f"Brands available: {', '.join(brands)}")
        return "\n".join(parts)
    return f'Sorry, no products match "{query}". Try "laptops" or "headphones".'


def format_products_response(products, user_message, intent):
    if not products:
        q, _ = clean_query(user_message)
        if q:
            return format_no_results(q)
        return "Try asking about something specific, like laptops or headphones."

    n = len(products)
    header = f"Found {n} product{'s' if n > 1 else ''} for you:"
    lines = [header, ""]

    if n == 1:
        lines.append(format_single_product(products[0]))
    else:
        lines.append(format_product_list(products, intent))

    if intent["cheap"]:
        p = products[0]
        price = p.discount_price if p.is_on_sale else p.price
        lines.append(f"  Tip: {p.name} at {format_currency(price)} is the most affordable.")
    elif intent["best"]:
        p = products[0]
        lines.append(f"  Tip: {p.name} ({p.average_rating}/5) is top rated.")

    return "\n".join(lines)


WELCOME_MESSAGE = """Welcome to ShopEase! I'm your shopping assistant.

Here's how I can help:
  1. Find products — "show laptops under $1500"
  2. Best deals — "cheapest headphones" or "best laptop"
  3. Product details — "tell me about ASUS ROG"
  4. Recommendations — just ask!

How can I help you today?"""


def generate_response(user_message, history_context=None):
    msg = user_message.lower().strip()

    if is_greeting(msg):
        return WELCOME_MESSAGE

    if is_help(msg):
        return WELCOME_MESSAGE

    if is_thanks(msg):
        return "You're welcome! Let me know if you need anything else."

    if is_exit(msg):
        return "Thanks for visiting ShopEase! Have a great day!"

    query, intent = clean_query(user_message)
    products = search_products(query, intent)
    return format_products_response(products, user_message, intent)


def get_chat_response(user_message, history_context=None):
    products_context = ""
    try:
        query, _ = clean_query(user_message)
        if not is_greeting(user_message) and not is_thanks(user_message) and not is_exit(user_message) and not is_help(user_message):
            products = search_products(query, {"cheap": False, "best": False})
            products_context = "\n".join(
                f"  - {p.name} — {format_currency(p.discount_price if p.is_on_sale else p.price)}"
                f" ({p.brand.name if p.brand else 'N/A'}, Rating: {p.average_rating}/5)"
                for p in products[:15]
            )
    except Exception:
        pass

    messages = []
    system_prompt = (
        "You are a friendly, concise shopping assistant for ShopEase e-commerce store. "
        "Keep responses short and helpful. Use the product data provided.\n\n"
        "Available products:\n"
        f"{products_context or 'No products retrieved.'}"
    )
    messages.append({"role": "system", "content": system_prompt})
    if history_context:
        for msg in history_context[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    prompt_text = ""
    for msg in messages:
        if msg["role"] == "system":
            prompt_text += f"<s>[INST] <<SYS>>\n{msg['content']}\n<</SYS>>\n"
        elif msg["role"] == "user":
            prompt_text += f"{msg['content']} [/INST]"
        elif msg["role"] == "assistant":
            prompt_text += f" {msg['content']} </s><s>[INST]"

    try:
        headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
        payload = {
            "inputs": prompt_text,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 0.95,
            },
        }
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("generated_text", "").replace(prompt_text, "").strip()
        return str(data)
    except Exception:
        return generate_response(user_message, history_context)
