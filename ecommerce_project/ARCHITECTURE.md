# ShopEase — Architecture & Deployment Guide

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────────────┐    │
│  │ Browser  │  │  Mobile  │  │   API    │  │   Bootstrap 5 + AJAX    │    │
│  │ (Django  │  │  (3rd-   │  │ Clients  │  │   + Fetch API (SPA)     │    │
│  │ Templates│  │  party)  │  │ (curl/   │  │                         │    │
│  │ )        │  │          │  │ Postman) │  │   - Smart Search        │    │
│  │          │  │          │  │          │  │   - Live Chatbot        │    │
│  │          │  │          │  │          │  │   - Async Cart          │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────────┬────────────┘    │
└───────┼─────────────┼─────────────┼─────────────────────┼──────────────────┘
        │             │             │                     │
        │        ┌────┴────┐   ┌────┴────┐          ┌─────┴─────┐
        │        │  JWT    │   │  JWT    │          │   AJAX    │
        │        │  Token  │   │  Token  │          │   Fetch   │
        │        └─────────┘   └─────────┘          └───────────┘
        ▼             ▼             ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                 │
│                                                                             │
│              ┌──────────────────────────────────────────┐                   │
│              │         /api/ (REST Framework)            │                   │
│              │   JWT Authentication (SimpleJWT)          │                   │
│              │   Permissions (AllowAny, IsAuthenticated, │                   │
│              │   IsAdminUser, IsAdminOrReadOnly,         │                   │
│              │   IsOwnerOrAdmin)                         │                   │
│              └──────┬───────────────────────┬───────────┘                   │
│                     │                       │                               │
│              ┌──────┴──────┐        ┌───────┴────────┐                      │
│              │  Public     │        │  Protected     │                      │
│              │  Endpoints  │        │  Endpoints     │                      │
│              │  - products │        │  - cart/*      │                      │
│              │  - search   │        │  - orders/*    │                      │
│              │  - categories│       │  - addresses/* │                      │
│              │  - brands   │        │  - notifications│                     │
│              │  - chat     │        │  - descriptions │                     │
│              │  - token/*  │        │  - profile     │                      │
│              └─────────────┘        └────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                     │
│                                                                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────┐     │
│  │ Recommendation  │  │   Smart Search   │  │  Description Generator│     │
│  │  Engine         │  │   Service        │  │   (OpenAI GPT-4o-mini) │     │
│  │                 │  │                  │  │                        │     │
│  │ - same category │  │ - AI intent      │  │ - product_name + brand │     │
│  │ - same brand    │  │   parsing        │  │ - specs list          │     │
│  │ - similar price │  │ - OR keyword     │  │ → marketing_desc      │     │
│  │ → weighted      │  │   fallback       │  │ → features[]          │     │
│  │   score ranking │  │ - relevance      │  │ → benefits[]          │     │
│  └────────┬────────┘  │   scoring        │  └───────────┬────────────┘     │
│           │           └────────┬─────────┘              │                  │
│           ▼                    ▼                         ▼                  │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     AI SERVICES (OpenAI)                            │    │
│  │  ┌──────────────┐  ┌───────────────┐  ┌────────────────────────┐  │    │
│  │  │  Chatbot     │  │  Analytics    │  │  Search Intent Parser  │  │    │
│  │  │  (GPT-4o-    │  │  (GPT-4o-     │  │  (GPT-4o-mini)        │  │    │
│  │  │   mini)      │  │   mini)       │  │                        │  │    │
│  │  │              │  │               │  │ extracts: category,    │  │    │
│  │  │ - product    │  │ - analyzes    │  │ brand, price range,    │  │    │
│  │  │   context    │  │   orders,     │  │ keywords, sort from    │  │    │
│  │  │ - chat       │  │   products,   │  │ natural language       │  │    │
│  │  │   history    │  │   revenue     │  │ queries                │  │    │
│  │  └──────────────┘  │ → insights[]  │  └────────────────────────┘  │    │
│  │                    └───────────────┘                               │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────────┐     │
│  │  Analytics       │  │  Notification  │  │  Recently Viewed       │     │
│  │  Service         │  │  Service       │  │  Tracker               │     │
│  │                  │  │                │  │                        │     │
│  │ - best sellers   │  │ - order placed │  │ - update_or_create     │     │
│  │ - top brands     │  │ - order approved│ │   on product detail    │     │
│  │ - revenue trends │  │ - order rejected│ │ - limit 10 per user    │     │
│  │ - order growth   │  │ - mark read    │  │ - unique constraint    │     │
│  │ - low stock      │  │                │  │                        │     │
│  └──────────────────┘  └────────────────┘  └────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                       │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │accounts  │  │ products │  │  cart    │  │  orders  │  │   chat       │ │
│  │          │  │          │  │          │  │          │  │              │ │
│  │- User    │  │- Product │  │- Cart    │  │- Order   │  │- ChatSession │ │
│  │ (built-  │  │- Category│  │- CartItem│  │- OrderItem│ │- ChatMessage │ │
│  │  in)     │  │- Brand   │  │          │  │          │  │              │ │
│  │- Customer│  │- Review  │  │          │  │          │  │              │ │
│  │  Profile │  │- Recently│  │          │  │          │  │              │ │
│  │- Address │  │  Viewed  │  │          │  │          │  │              │ │
│  │- Payment │  │          │  │          │  │          │  │              │ │
│  │  Method  │  │          │  │          │  │          │  │              │ │
│  │- Laptop  │  │          │  │          │  │          │  │              │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐                                        │
│  │   dashboard  │  │   wishlist   │                                        │
│  │              │  │              │                                        │
│  │ - Notification│ │ - Wishlist   │                                        │
│  │              │  │ - WishlistItem│                                       │
│  └──────────────┘  └──────────────┘                                        │
│                                                                             │
│  Database: SQLite (dev) / PostgreSQL (prod)                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
ecommerce_project/
├── manage.py                          # Django CLI entry point
│
├── ecommerce_project/                 # Project configuration (Django project root)
│   ├── __init__.py
│   ├── settings.py                    # DRF, JWT, OpenAI, database config
│   ├── urls.py                        # Root URL conf (includes api/, admin/, apps)
│   ├── wsgi.py                        # WSGI entry point for production
│   ├── asgi.py                        # ASGI entry point (future WebSocket support)
│   ├── api_urls.py                    # Master API route table (all endpoints)
│   ├── api_views.py                   # Centralized REST API views
│   ├── serializers.py                 # All DRF serializers (cross-app)
│   └── permissions.py                 # Custom permission classes
│
├── accounts/                          # User management app
│   ├── models.py                      # CustomerProfile, Address, PaymentMethod, Laptop
│   ├── views.py                       # Login, Register, Profile, Address CRUD
│   ├── urls.py                        # App-specific routes
│   ├── admin.py                       # Admin config for user data
│   ├── forms.py                       # Login, Registration, Profile, Address forms
│   ├── signals.py                     # Auto-create CustomerProfile on registration
│   └── apps.py
│
├── products/                          # Product catalog app
│   ├── models.py                      # Product, Category, Brand, Review, RecentlyViewed
│   ├── views.py                       # Product list/detail, home page, review submission
│   ├── urls.py                        # App-specific routes
│   ├── admin.py                       # Admin config with image previews
│   ├── forms.py                       # Review form
│   ├── templatetags/
│   │   └── product_tags.py            # Custom template filter: image_url
│   ├── management/commands/
│   │   └── seed_laptops.py            # Database seeder (12 laptops)
│   └── services/                      # *** SERVICE LAYER ***
│       ├── __init__.py
│       ├── recommendation_service.py   # Weighted product recommendations
│       ├── search_service.py           # AI-powered smart search
│       └── description_generator.py    # AI product description generation
│
├── cart/                              # Shopping cart app
│   ├── models.py                      # Cart, CartItem
│   ├── views.py                       # Cart add/update/remove (Django views)
│   ├── urls.py
│   ├── context_processors.py          # Cart item count for navbar
│   ├── utils.py                       # Cart helper utilities
│   └── admin.py
│
├── orders/                            # Order management app
│   ├── models.py                      # Order (status workflow), OrderItem
│   ├── views.py                       # Checkout, order detail (Django views)
│   ├── urls.py
│   ├── forms.py                       # Checkout form
│   └── admin.py
│
├── dashboard/                         # Staff admin dashboard app
│   ├── models.py                      # Notification
│   ├── views.py                       # Dashboard, order review, notifications
│   ├── urls.py
│   ├── context_processors.py          # Notification counts for navbar
│   ├── admin.py
│   └── services/                      # *** SERVICE LAYER ***
│       ├── __init__.py
│       └── analytics_service.py       # Sales analytics + AI insights
│
├── chat/                              # AI chatbot app
│   ├── models.py                      # ChatSession, ChatMessage
│   ├── api_views.py                   # Chat REST endpoint
│   ├── api_urls.py
│   ├── admin.py                       # Chat history admin
│   └── services/
│       ├── __init__.py
│       └── openai_service.py          # OpenAI integration with product context
│
├── wishlist/                          # Wishlist app
│   ├── models.py                      # Wishlist, WishlistItem
│   ├── views.py
│   ├── urls.py
│   ├── context_processors.py
│   └── admin.py
│
├── templates/                         # Django template files
│   ├── base.html                      # Root template (Bootstrap 5, navbar, footer, chatbot)
│   ├── navbar.html                    # Responsive nav with smart search bar
│   ├── footer.html                    # Site footer
│   ├── chatbot.html                   # Floating chatbot widget (button + window + JS)
│   ├── accounts/                      # Login, register, profile, address forms
│   ├── products/                      # Home, product list, product detail
│   ├── cart/                          # Cart detail
│   ├── orders/                        # Checkout, order detail, order complete
│   ├── dashboard/                     # Dashboard home, order review, notifications, desc gen
│   └── wishlist/                      # Wishlist list
│
├── static/                            # Static files
│   ├── css/style.css                  # Custom styles (chatbot, cards, dashboard, etc.)
│   ├── js/script.js                   # JavaScript (alert dismiss, smart search, bot)
│   └── images/placeholder.svg         # Placeholder for missing images
│
├── media/                             # User-uploaded media (images, QR codes)
│   ├── products/
│   ├── categories/
│   └── payment_qrcodes/
│
└── db.sqlite3                         # SQLite database (development)
```

---

## Services Layer

All business logic is extracted into service modules, keeping views thin and testable.

### 1. `products/services/recommendation_service.py`

**Purpose:** Recommend similar products based on category, brand, and price proximity.

```
Algorithm:
  For each candidate product:
    +3 if same category as source product
    +2 if same brand as source product
    +1 if price is within 50%-200% of source product price
  Sort by total score, return top 4
  Fallback: most recent 4 active products if no scored matches
```

**Functions:**
```python
get_recommendations(product, limit=4) -> List[Product]
get_recently_viewed(user, limit=10) -> List[Product]
```

### 2. `products/services/search_service.py`

**Purpose:** Natural language product search with AI intent parsing.

```
Tier 1 — AI Parse:
  User query → OpenAI GPT-4o-mini → structured JSON:
    {category, brand, max_price, min_price, keywords[], sort}
  Django ORM filters products by extracted criteria
  Results are scored by keyword density in name > brand > category > description
  If 0 results, fall through to Tier 2

Tier 2 — Keyword Fallback:
  Split query into words
  Filter stopwords (a, an, the, for, best, cheap, etc.)
  OR-match across name, description, category, brand
```

**Functions:**
```python
smart_search(query: str) -> List[Product]
```

### 3. `products/services/description_generator.py`

**Purpose:** AI-powered marketing description generation for admin.

```
Input:  product_name, brand, specs_list[]
OpenAI prompt → structured JSON response:
  {marketing_description, features[], benefits[]}
Returns parsed JSON object
```

**Functions:**
```python
generate_description(product_name, brand, specs_list) -> dict
```

### 4. `chat/services/openai_service.py`

**Purpose:** AI shopping assistant chatbot with live product context.

```
Flow:
  1. User sends message → POST /api/chat/
  2. search_products() queries database for relevant products
     - Parses tokens for price filters (under $X, $Y, above $Z)
     - Searches across name, description, category, brand
  3. System prompt built with real-time product data
  4. Chat history appended (last 10 messages)
  5. OpenAI responds with natural language answer
  6. Response saved to ChatMessage and returned
```

**Functions:**
```python
search_products(query) -> List[Product]
format_products_for_prompt(products) -> str
get_chat_response(user_message, history) -> str
```

### 5. `dashboard/services/analytics_service.py`

**Purpose:** Sales analytics with AI-generated business insights.

```
Data Queries:
  - get_best_selling_products():  Top 5 by quantity sold
  - get_top_brands():             Top 5 by revenue
  - get_revenue_trends():         Monthly revenue (last 6 months)
  - get_order_growth():           Monthly order count (last 6 months)
  - get_low_stock_alerts():       Products below stock threshold

AI Insights:
  All above data → OpenAI prompt → 3-5 business insight strings
```

**Functions:**
```python
get_best_selling_products(limit=5) -> List[dict]
get_top_brands(limit=5) -> List[dict]
get_revenue_trends(months=6) -> List[dict]
get_order_growth(months=6) -> List[dict]
get_low_stock_alerts(threshold=5) -> List[dict]
get_ai_insights() -> List[str]
get_full_analytics() -> dict
```

### 6. Cross-cutting: Recently Viewed Tracker

**Location:** `products/views.py` (inline in ProductDetailView)

```python
RecentlyViewed.objects.update_or_create(
    user=request.user,
    product=product,
    defaults={'viewed_at': None}
)
```

---

## API Layer

All REST endpoints are defined in `ecommerce_project/api_urls.py` with views in `ecommerce_project/api_views.py`. Authentication is handled by `rest_framework_simplejwt` (Bearer JWT tokens).

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/token/` | None | Obtain JWT access + refresh tokens |
| POST | `/api/token/refresh/` | None | Refresh expired access token |

### Products

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/products/` | AllowAny | Paginated product list |
| GET | `/api/products/{id}/` | AllowAny | Product detail with category/brand objects |
| GET | `/api/products/{id}/recommendations/` | AllowAny | Top 4 recommended products |

### Search

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/search/?q=` | AllowAny | AI-powered smart search |

### Categories & Brands

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/categories/` | AllowAny | All categories |
| GET | `/api/brands/` | AllowAny | All brands |

### Cart

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/cart/` | IsAuthenticated | Current user's cart with items |
| POST | `/api/cart/add/` | IsAuthenticated | Add product to cart |
| PUT | `/api/cart/update/` | IsAuthenticated | Update item quantity (0 = remove) |
| DELETE | `/api/cart/remove/` | IsAuthenticated | Remove item from cart |

### Orders

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/orders/` | IsAuthenticated | User's order list |
| POST | `/api/orders/create/` | IsAuthenticated | Create order from cart |
| GET | `/api/orders/{id}/` | IsAuthenticated | Order detail |

### Addresses

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/addresses/` | IsAuthenticated | User's addresses |
| POST | `/api/addresses/` | IsAuthenticated | Create address |
| PUT | `/api/addresses/{id}/` | IsAuthenticated | Update address |
| DELETE | `/api/addresses/{id}/` | IsAuthenticated | Delete address |

### Notifications

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/notifications/` | IsAuthenticated | User's notifications |

### Chatbot

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/chat/` | AllowAny | Send message, get AI reply |

### Description Generator (Admin)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/descriptions/generate/` | IsAdminUser | Generate AI product description |

### Permission Model

| Class | Behavior |
|-------|----------|
| `AllowAny` | No authentication required |
| `IsAuthenticated` | Valid JWT required |
| `IsAdminUser` | `is_staff=True` required |
| `IsAdminOrReadOnly` | Anyone can read, only staff can write |
| `IsOwnerOrAdmin` | Staff can access all; regular users can only access own objects |

---

## Data Model Relationships

```
User (django.contrib.auth)
├── CustomerProfile        (OneToOne → accounts)
├── Address[]              (ForeignKey → accounts)
├── Cart                   (OneToOne → cart)
├── Order[]                (ForeignKey → orders)
├── Notification[]         (ForeignKey → dashboard)
├── ChatSession[]          (ForeignKey → chat)
├── RecentlyViewed[]       (ForeignKey → products)
└── Review[]               (ForeignKey → products)

Product
├── Category               (ForeignKey → products)
├── Brand                  (ForeignKey → products)
├── Review[]               (Reverse FK → products)
├── CartItem[]             (Reverse FK → cart)
├── OrderItem[]            (Reverse FK → orders)
├── WishlistItem[]         (Reverse FK → wishlist)
└── RecentlyViewed[]       (Reverse FK → products)

Order
├── OrderItem[]            (Cascade → orders)
├── PaymentMethod          (SET_NULL → accounts)
└── Notification[]         (Cascade → dashboard)

ChatSession
└── ChatMessage[]          (Cascade → chat)
```

---

## Key Architectural Decisions

### Why Centralized API Views?
All REST endpoints live in `ecommerce_project/api_views.py` rather than being spread across apps. This provides a single source of truth for API behavior, simplifies permission auditing, and makes it easy to see all endpoints in one place.

### Why Service Layer?
Business logic (recommendations, search, analytics, AI calls) is extracted into `*/services/*.py` modules. Views never call OpenAI or construct complex queries directly. This makes the code testable — you can unit test `recommendation_service.get_recommendations()` without touching HTTP.

### Why JWT Authentication
JWT (via `rest_framework_simplejwt`) enables stateless authentication. The frontend stores the token and sends it with every request via `Authorization: Bearer <token>`. No session cookies needed for API calls. Sessions are still used for Django template views (login state).

### Why Dual Search (AI + Keyword)
Pure AI search is slow (~1s per query) and expensive. Pure keyword search misses intent. The hybrid approach uses AI only to extract structured intent, then delegates the actual search to Django ORM which runs in milliseconds.

### Why In-App Notifications Over Email/SMS
The Notification model is simple and synchronous. When an order is placed/approved/rejected, a Notification object is created. The dashboard displays unread notifications. This avoids the complexity of email/SMS integration while providing real-time feedback in the app.

---

## Deployment Guide

### Prerequisites

- Python 3.12+
- pip
- Git
- PostgreSQL (production) / SQLite (development)
- OpenAI API key (for AI features)

### Development Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd ecommerce_project

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
#    Create .env file or set directly:
export SECRET_KEY='your-secret-key'
export DEBUG=True
export OPENAI_API_KEY='sk-...'
export DATABASE_URL='sqlite:///db.sqlite3'

# 5. Run migrations
python manage.py migrate

# 6. Seed sample data (optional)
python manage.py seed_laptops

# 7. Create admin user
python manage.py createsuperuser

# 8. Collect static files
python manage.py collectstatic

# 9. Start development server
python manage.py runserver
```

### Production Deployment (Linux/Ubuntu)

```bash
# 1. System dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib

# 2. Create PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE ecommerce;"
sudo -u postgres psql -c "CREATE USER ecommerce_user WITH PASSWORD 'strong_password';"
sudo -u postgres psql -c "ALTER ROLE ecommerce_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE ecommerce_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE ecommerce_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ecommerce TO ecommerce_user;"

# 3. Clone and setup project
cd /var/www
git clone <repo-url>
cd ecommerce_project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt

# 4. Configure environment
cat > .env <<EOF
SECRET_KEY='<generated-secret-key>'
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
OPENAI_API_KEY='sk-...'
DB_NAME=ecommerce
DB_USER=ecommerce_user
DB_PASSWORD=strong_password
DB_HOST=localhost
DB_PORT=5432
EOF

# 5. Update settings.py for PostgreSQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST'),
#         'PORT': config('DB_PORT'),
#     }
# }

# 6. Run migrations and collect static
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# 7. Configure Gunicorn
pip install gunicorn
sudo nano /etc/systemd/system/gunicorn.service
```

**gunicorn.service:**
```ini
[Unit]
Description=gunicorn daemon for ecommerce_project
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ecommerce_project
ExecStart=/var/www/ecommerce_project/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/ecommerce_project/ecommerce_project.sock \
    ecommerce_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# 8. Configure Nginx
sudo nano /etc/nginx/sites-available/ecommerce
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/ecommerce_project/staticfiles/;
    }

    location /media/ {
        alias /var/www/ecommerce_project/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/ecommerce_project/ecommerce_project.sock;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# 9. Configure SSL with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 10. Security hardening
# settings.py production overrides:
# DEBUG = False
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
```

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | Django secret key (generate with `openssl rand -hex 32`) |
| `DEBUG` | No | `True` | Debug mode (must be `False` in production) |
| `ALLOWED_HOSTS` | No | `[]` | Comma-separated hostnames |
| `OPENAI_API_KEY` | No | — | OpenAI API key (AI features disabled without it) |
| `DB_NAME` | No | — | PostgreSQL database name |
| `DB_USER` | No | — | PostgreSQL user |
| `DB_PASSWORD` | No | — | PostgreSQL password |
| `DB_HOST` | No | `localhost` | PostgreSQL host |
| `DB_PORT` | No | `5432` | PostgreSQL port |

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ecommerce_project.wsgi:application"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ecommerce
      POSTGRES_USER: ecommerce_user
      POSTGRES_PASSWORD: strong_password

  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             gunicorn --bind 0.0.0.0:8000 ecommerce_project.wsgi:application"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      SECRET_KEY: "${SECRET_KEY}"
      DEBUG: "False"
      ALLOWED_HOSTS: "${ALLOWED_HOSTS}"
      OPENAI_API_KEY: "${OPENAI_API_KEY}"
      DB_NAME: ecommerce
      DB_USER: ecommerce_user
      DB_PASSWORD: strong_password
      DB_HOST: db
      DB_PORT: 5432
    depends_on:
      - db

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Performance Considerations

- **Database queries:** All list views use `select_related()` and `prefetch_related()` to avoid N+1 queries
- **Pagination:** DRF pagination is enabled by default (page size 20)
- **Search:** AI parsing takes ~500ms, but ORM execution takes <10ms — the hybrid approach minimizes OpenAI calls
- **Static files:** Use a CDN (CloudFront, CloudFlare) for static/media files in production
- **Caching:** Consider Redis for session caching and API response caching for product lists
- **Workers:** Gunicorn with 3 workers handles moderate traffic. Scale workers = (2 × CPU cores) + 1

### Monitoring

- **Logging:** Check `gunicorn` logs at `/var/log/gunicorn/`
- **Error tracking:** Integrate Sentry (`pip install sentry-sdk`)
- **Performance:** Django Debug Toolbar (development only)
- **Database:** `pg_stat_statements` for query profiling (PostgreSQL)

### Key Files Reference

| File | Purpose |
|------|---------|
| `ecommerce_project/settings.py` | All configuration in one file |
| `ecommerce_project/urls.py` | Root URL dispatch |
| `ecommerce_project/api_urls.py` | Complete API route table |
| `ecommerce_project/api_views.py` | All REST view implementations |
| `ecommerce_project/serializers.py` | All request/response serializers |
| `ecommerce_project/permissions.py` | Custom permission classes |
| `products/services/recommendation_service.py` | Recommendation engine |
| `products/services/search_service.py` | Smart search with AI |
| `products/services/description_generator.py` | AI description generation |
| `chat/services/openai_service.py` | Chatbot AI service |
| `dashboard/services/analytics_service.py` | Analytics + AI insights |
| `templates/base.html` | Root template layout |
| `templates/chatbot.html` | Floating chatbot widget |
| `static/js/script.js` | Smart search + chatbot JS |
| `static/css/style.css` | All custom styles |
