from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard_home'),
    path('orders/review/', views.OrderReviewListView.as_view(), name='order_review_list'),
    path('orders/review/<int:pk>/', views.OrderReviewDetailView.as_view(), name='order_review_detail'),
    path('orders/<int:pk>/', views.OrderDashboardDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/approve/', views.ApproveOrderView.as_view(), name='approve_order'),
    path('orders/<int:pk>/reject/', views.RejectOrderView.as_view(), name='reject_order'),
    path('notifications/', views.UserNotificationListView.as_view(), name='user_notifications'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('generate-description/', views.GenerateDescriptionView.as_view(), name='generate_description'),
    # Product Management
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    # Brand Management
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<int:pk>/edit/', views.BrandUpdateView.as_view(), name='brand_edit'),
    path('brands/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),
    # Category Management
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]
