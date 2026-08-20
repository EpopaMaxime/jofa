from django.views.generic import ListView, DetailView
from .models import Category, Product
from django.db.models import Q

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(available=True).select_related('vendor', 'category')
        category_slug = self.request.GET.get('category')
        skin_type = self.request.GET.get('skin_type')
        vendor_slug = self.request.GET.get('vendor')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        sort = self.request.GET.get('sort')
        query = self.request.GET.get('q')

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if skin_type:
            queryset = queryset.filter(skin_type=skin_type)
        if vendor_slug:
            queryset = queryset.filter(vendor__slug=vendor_slug, vendor__status='approved', vendor__is_active=True)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(vendor__store_name__icontains=query)
            )

        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['skin_types'] = Product.SKIN_TYPE_CHOICES
        try:
            from vendors.models import Vendor
            context['vendors'] = Vendor.objects.filter(is_active=True, status='approved')
        except Exception:
            context['vendors'] = []
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.filter(approved=True)
        try:
            from recommendations.engine import RecommendationEngine
            context['recommended_products'] = RecommendationEngine().complementary_for_product(
                self.object, limit=4
            )
        except Exception:
            context['recommended_products'] = []
        return context
