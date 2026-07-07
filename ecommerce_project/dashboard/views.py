from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import FormView

from orders.models import Order

from .models import Notification
from .services.analytics_service import get_full_analytics

User = get_user_model()
LOW_STOCK_THRESHOLD = 5


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        base_orders = Order.objects.all()

        context['total_products'] = 0  # computed later if needed
        context['total_categories'] = 0
        context['total_orders'] = base_orders.count()
        context['total_users'] = User.objects.count()
        context['pending_orders'] = base_orders.filter(status=Order.Status.PENDING).count()
        context['approved_orders'] = base_orders.filter(status=Order.Status.APPROVED).count()
        context['rejected_orders'] = base_orders.filter(status=Order.Status.REJECTED).count()
        context['processing_orders'] = base_orders.filter(status=Order.Status.PROCESSING).count()

        context['revenue'] = base_orders.exclude(
            status__in=[Order.Status.CANCELLED, Order.Status.REJECTED, Order.Status.PENDING]
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_orders = (
            base_orders
            .filter(created_at__gte=six_months_ago)
            .exclude(status__in=[Order.Status.CANCELLED, Order.Status.REJECTED])
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('total_amount'), count=Count('id'))
            .order_by('month')
        )

        labels = []
        data = []
        for entry in monthly_orders:
            labels.append(entry['month'].strftime('%b %Y'))
            data.append(float(entry['total']))

        context['chart_labels'] = labels
        context['chart_data'] = data

        context['recent_orders'] = base_orders.select_related('user').all()[:5]

        from products.models import Product
        context['low_stock_products'] = Product.objects.filter(
            stock__lt=LOW_STOCK_THRESHOLD
        ).order_by('stock')

        context['total_products'] = Product.objects.count()
        context['total_categories'] = 0
        from products.models import Category
        context['total_categories'] = Category.objects.count()

        context['unread_notifications'] = Notification.objects.filter(
            user__isnull=True, is_read=False
        ).select_related('related_order')

        context['all_notifications'] = Notification.objects.filter(
            user__isnull=True
        ).select_related('related_order')[:10]

        analytics = get_full_analytics()
        context['best_sellers'] = analytics['best_sellers']
        context['top_brands'] = analytics['top_brands']
        context['sales_chart_labels'] = [t['month'].strftime('%b %Y') for t in analytics['revenue_trends']]
        context['sales_chart_data'] = [float(t['revenue']) for t in analytics['revenue_trends']]
        context['orders_chart_labels'] = [t['month'].strftime('%b %Y') for t in analytics['order_growth']]
        context['orders_chart_data'] = [t['count'] for t in analytics['order_growth']]

        return context


class OrderReviewListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = 'dashboard/order_review_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        return Order.objects.filter(
            status=Order.Status.PENDING
        ).select_related('user', 'payment_method').prefetch_related('items__product')


class OrderReviewDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = 'dashboard/order_review_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(
            status=Order.Status.PENDING
        ).select_related('user', 'payment_method').prefetch_related('items__product')


class OrderDashboardDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = 'dashboard/order_review_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.select_related(
            'user', 'payment_method'
        ).prefetch_related('items__product')


class ApproveOrderView(StaffRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, status=Order.Status.PENDING)

        order.status = Order.Status.APPROVED
        order.save()

        Notification.objects.filter(
            related_order=order, user__isnull=True, is_read=False
        ).update(is_read=True)

        Notification.objects.create(
            user=order.user,
            title='Order Approved',
            message=(
                f"Your order #{order.order_number} has been approved "
                f"and is being processed."
            ),
            related_order=order,
        )

        messages.success(request, f'Order #{order.order_number} has been approved.')
        return redirect('dashboard:order_review_list')


class RejectOrderView(StaffRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, status=Order.Status.PENDING)

        order.status = Order.Status.REJECTED
        order.save()

        Notification.objects.filter(
            related_order=order, user__isnull=True, is_read=False
        ).update(is_read=True)

        Notification.objects.create(
            user=order.user,
            title='Order Rejected',
            message=(
                f"Unfortunately, your order #{order.order_number} was rejected. "
                f"Please contact support."
            ),
            related_order=order,
        )

        messages.success(request, f'Order #{order.order_number} has been rejected.')
        return redirect('dashboard:order_review_list')


class UserNotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'dashboard/user_notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('related_order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        ).count()
        return context


class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, user=request.user
        )
        notification.is_read = True
        notification.save()
        return redirect('dashboard:user_notifications')


class GenerateDescriptionView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/generate_description.html'
