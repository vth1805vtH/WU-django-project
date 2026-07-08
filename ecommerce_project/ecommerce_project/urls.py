from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from products.views import HomePageView
from .api_views import bootstrap_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('api/', include('ecommerce_project.api_urls', namespace='api')),
    path('bootstrap/', bootstrap_view, name='bootstrap'),
    path('', HomePageView.as_view(), name='home'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
