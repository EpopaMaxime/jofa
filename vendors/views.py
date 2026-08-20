from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Count, Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from orders.models import OrderItem
from products.models import Product

from .forms import (
    VendorOpenStoreForm,
    VendorProductForm,
    VendorProfileForm,
    VendorRegistrationForm,
)
from .mixins import VendorRequiredMixin, get_vendor_or_none
from .models import Vendor


class VendorLandingView(TemplateView):
    template_name = 'vendors/landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = Vendor.objects.filter(
            is_active=True, status='approved'
        ).annotate(live_products=Count('products', filter=Q(products__available=True)))[:12]
        context['user_vendor'] = get_vendor_or_none(self.request.user)
        return context


class VendorRegisterView(FormView):
    template_name = 'vendors/register.html'
    form_class = VendorRegistrationForm
    success_url = reverse_lazy('vendors:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if get_vendor_or_none(request.user):
                return redirect('vendors:dashboard')
            return redirect('vendors:open_store')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            'Welcome seller! Your store is live — start adding products.',
        )
        return super().form_valid(form)


class VendorOpenStoreView(LoginRequiredMixin, FormView):
    """Logged-in shopper becomes a seller without creating a second account."""

    template_name = 'vendors/open_store.html'
    form_class = VendorOpenStoreForm
    success_url = reverse_lazy('vendors:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if get_vendor_or_none(request.user):
            return redirect('vendors:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        vendor = form.save(commit=False)
        vendor.user = self.request.user
        vendor.email = self.request.user.email
        vendor.status = 'approved'
        vendor.is_active = True
        vendor.save()
        messages.success(self.request, 'Your seller store is live!')
        return super().form_valid(form)


class VendorPendingView(TemplateView):
    template_name = 'vendors/pending.html'


class VendorSuspendedView(TemplateView):
    template_name = 'vendors/suspended.html'


class VendorDashboardView(VendorRequiredMixin, TemplateView):
    template_name = 'vendors/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.get_vendor()
        products = vendor.products.all()
        items = OrderItem.objects.filter(vendor=vendor).select_related(
            'order', 'product'
        )
        revenue = (
            items.exclude(fulfillment_status='cancelled').aggregate(
                total=Sum('price')
            )  # rough; better compute price*qty in Python
        )
        total_revenue = sum(
            i.get_cost()
            for i in items.exclude(fulfillment_status='cancelled')
        )
        context.update(
            {
                'vendor': vendor,
                'product_count': products.count(),
                'live_count': products.filter(available=True).count(),
                'order_item_count': items.count(),
                'pending_fulfillment': items.filter(fulfillment_status='pending').count(),
                'total_revenue': total_revenue,
                'recent_items': items.order_by('-id')[:8],
                'recent_products': products.order_by('-created_at')[:6],
            }
        )
        return context


class VendorProductListView(VendorRequiredMixin, ListView):
    template_name = 'vendors/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        return self.get_vendor().products.select_related('category').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.get_vendor()
        return context


class VendorProductCreateView(VendorRequiredMixin, CreateView):
    model = Product
    form_class = VendorProductForm
    template_name = 'vendors/product_form.html'
    success_url = reverse_lazy('vendors:product_list')

    def form_valid(self, form):
        product = form.save(commit=False)
        product.vendor = self.get_vendor()
        product.featured = False
        product.save()
        messages.success(self.request, f'“{product.name}” is now listed in your store.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.get_vendor()
        context['title'] = 'Add product'
        return context


class VendorProductUpdateView(VendorRequiredMixin, UpdateView):
    model = Product
    form_class = VendorProductForm
    template_name = 'vendors/product_form.html'
    success_url = reverse_lazy('vendors:product_list')

    def get_queryset(self):
        return self.get_vendor().products.all()

    def form_valid(self, form):
        messages.success(self.request, 'Product updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.get_vendor()
        context['title'] = 'Edit product'
        return context


class VendorProductDeleteView(VendorRequiredMixin, DeleteView):
    model = Product
    template_name = 'vendors/product_confirm_delete.html'
    success_url = reverse_lazy('vendors:product_list')

    def get_queryset(self):
        return self.get_vendor().products.all()

    def form_valid(self, form):
        messages.success(self.request, 'Product removed from your store.')
        return super().form_valid(form)


class VendorOrderListView(VendorRequiredMixin, ListView):
    template_name = 'vendors/order_list.html'
    context_object_name = 'items'
    paginate_by = 30

    def get_queryset(self):
        return (
            OrderItem.objects.filter(vendor=self.get_vendor())
            .select_related('order', 'product', 'order__user')
            .order_by('-id')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.get_vendor()
        context['status_choices'] = OrderItem._meta.get_field('fulfillment_status').choices
        return context


class VendorOrderItemUpdateView(VendorRequiredMixin, View):
    def post(self, request, pk):
        vendor = self.get_vendor()
        item = get_object_or_404(OrderItem, pk=pk, vendor=vendor)
        status = request.POST.get('fulfillment_status')
        allowed = {c[0] for c in OrderItem._meta.get_field('fulfillment_status').choices}
        if status in allowed:
            item.fulfillment_status = status
            item.save(update_fields=['fulfillment_status'])
            messages.success(request, f'Order item #{item.id} marked {status}.')
        else:
            messages.error(request, 'Invalid status.')
        return redirect('vendors:orders')


class VendorProfileUpdateView(VendorRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorProfileForm
    template_name = 'vendors/profile_edit.html'
    success_url = reverse_lazy('vendors:dashboard')

    def get_object(self, queryset=None):
        return self.get_vendor()

    def form_valid(self, form):
        messages.success(self.request, 'Store profile updated.')
        return super().form_valid(form)


class VendorStorefrontView(DetailView):
    model = Vendor
    slug_field = 'slug'
    template_name = 'vendors/storefront.html'
    context_object_name = 'vendor'

    def get_queryset(self):
        return Vendor.objects.filter(is_active=True, status='approved')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.products.filter(available=True)
        return context


class VendorDirectoryView(ListView):
    model = Vendor
    template_name = 'vendors/directory.html'
    context_object_name = 'vendors'
    paginate_by = 24

    def get_queryset(self):
        qs = Vendor.objects.filter(is_active=True, status='approved').annotate(
            live_products=Count('products', filter=Q(products__available=True))
        )
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(store_name__icontains=q)
                | Q(description__icontains=q)
                | Q(city__icontains=q)
            )
        return qs.order_by('-is_featured', 'store_name')
