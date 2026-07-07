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
]
