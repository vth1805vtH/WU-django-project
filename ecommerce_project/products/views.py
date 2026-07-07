from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .forms import ReviewForm
from .models import Brand, Category, Product, RecentlyViewed, Review
from .services.recommendation_service import get_recommendations
from .services.search_service import smart_search


class HomePageView(ListView):
    model = Product
    template_name = 'products/home.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')[:8]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')

        brand_slug = self.request.GET.get('brand')
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)

        query = self.request.GET.get('q', '').strip()
        if query:
            results = smart_search(query)
            pks = [p.pk for p in results]
            queryset = Product.objects.filter(pk__in=pks, is_active=True)
            if pks:
                preserved = Case(*[When(pk=pk, then=Value(i)) for i, pk in enumerate(pks)])
                queryset = queryset.order_by(preserved)

        sort = self.request.GET.get('sort', '-created_at')
        valid_sort_fields = {
            'created_at', '-created_at', 'name', '-name', 'price', '-price',
        }
        if sort in valid_sort_fields:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.annotate(
            product_count=Count('products')
        )
        context['current_brand'] = self.request.GET.get('brand', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        context['current_query'] = self.request.GET.get('q', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        product = get_object_or_404(
            Product.objects.select_related('category').prefetch_related('reviews__user'),
            slug=self.kwargs['slug'],
            is_active=True,
        )
        if self.request.user.is_authenticated:
            RecentlyViewed.objects.update_or_create(
                user=self.request.user,
                product=product,
                defaults={'viewed_at': timezone.now()},
            )
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all()
        context['review_form'] = ReviewForm()
        if self.request.user.is_authenticated:
            user_review = self.object.reviews.filter(user=self.request.user).first()
            context['user_review'] = user_review
        context['recommendations'] = get_recommendations(self.object)
        return context


@login_required
@require_POST
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    form = ReviewForm(request.POST)
    if form.is_valid():
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': form.cleaned_data['rating'],
                'comment': form.cleaned_data['comment'],
            },
        )
        messages.success(request, 'Your review has been submitted.')
    else:
        messages.error(request, 'Please fix the errors below.')
    return redirect(reverse('products:product_detail', args=[product.slug]))
