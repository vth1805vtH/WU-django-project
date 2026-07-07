from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.CheckoutView.as_view(), name='order_create'),
    path('complete/', views.OrderCompleteView.as_view(), name='order_complete'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/confirm-received/', views.ConfirmReceivedView.as_view(), name='confirm_received'),
]
