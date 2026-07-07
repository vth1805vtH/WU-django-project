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
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from orders.models import Order
from products.models import Brand, Category, Product

from .forms import BrandForm, CategoryForm, ProductForm
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


# ─── Product Management ───────────────────────────────────────────────

class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'dashboard/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('category', 'brand').all()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class ProductCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product created successfully.')
        return super().form_valid(form)


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product updated successfully.')
        return super().form_valid(form)


class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'dashboard/product_confirm_delete.html'
    success_url = reverse_lazy('dashboard:product_list')
    context_object_name = 'product'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Product deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ─── Brand Management ─────────────────────────────────────────────────

class BrandListView(StaffRequiredMixin, ListView):
    model = Brand
    template_name = 'dashboard/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 20

    def get_queryset(self):
        qs = Brand.objects.annotate(product_count=Count('products')).all()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class BrandCreateView(StaffRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'dashboard/brand_form.html'
    success_url = reverse_lazy('dashboard:brand_list')

    def form_valid(self, form):
        messages.success(self.request, 'Brand created successfully.')
        return super().form_valid(form)


class BrandUpdateView(StaffRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'dashboard/brand_form.html'
    success_url = reverse_lazy('dashboard:brand_list')

    def form_valid(self, form):
        messages.success(self.request, 'Brand updated successfully.')
        return super().form_valid(form)


class BrandDeleteView(StaffRequiredMixin, DeleteView):
    model = Brand
    template_name = 'dashboard/brand_confirm_delete.html'
    success_url = reverse_lazy('dashboard:brand_list')
    context_object_name = 'brand'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Brand deleted successfully.')
        return super().delete(request, *args, **kwargs)


# ─── Category Management ──────────────────────────────────────────────

class CategoryListView(StaffRequiredMixin, ListView):
    model = Category
    template_name = 'dashboard/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        qs = Category.objects.annotate(product_count=Count('products')).all()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class CategoryCreateView(StaffRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('dashboard:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)


class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('dashboard:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully.')
        return super().form_valid(form)


class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Category
    template_name = 'dashboard/category_confirm_delete.html'
    success_url = reverse_lazy('dashboard:category_list')
    context_object_name = 'category'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Category deleted successfully.')
        return super().delete(request, *args, **kwargs)
