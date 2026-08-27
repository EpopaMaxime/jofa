from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .access import remember_guest_order, user_can_access_order
from .cart import Cart
from products.models import Product, Coupon
from .models import Order, OrderItem
from django.urls import reverse_lazy
from rewards.utils import award_points, get_user_points
from rewards.models import RewardPoint

class CartAddView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        cart.add(product=product, quantity=quantity)
        return redirect('orders:cart_detail')

class CartRemoveView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)
        return redirect('orders:cart_detail')

class CartDetailView(TemplateView):
    template_name = 'orders/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['available_points'] = get_user_points(self.request.user)
        else:
            context['available_points'] = 0
        from rewards.models import RewardSetting
        setting = RewardSetting.objects.first()
        context['points_to_cash_ratio'] = setting.points_to_cash_ratio if setting else 0
        return context

class RedeemPointsView(LoginRequiredMixin, View):
    def post(self, request):
        cart = Cart(request)
        points_to_redeem = request.POST.get('points')
        
        try:
            points_to_redeem = int(points_to_redeem)
        except (ValueError, TypeError):
            points_to_redeem = 0

        available_points = get_user_points(request.user)

        if points_to_redeem > 0 and points_to_redeem <= available_points:
            cart.apply_points(points_to_redeem)
            from django.contrib import messages
            messages.success(request, f'Successfully applied {points_to_redeem} points to your cart.')
        else:
            cart.apply_points(0)
            from django.contrib import messages
            messages.error(request, 'Invalid points amount.')
        
        return redirect('orders:cart_detail')


class CouponApplyView(View):
    def post(self, request):
        code = request.POST.get('code')
        cart = Cart(request)
        if cart.apply_coupon(code):
            from django.contrib import messages
            messages.success(request, f'Coupon "{code}" applied successfully!')
        else:
            from django.contrib import messages
            messages.error(request, 'Invalid or expired coupon code.')
        return redirect('orders:cart_detail')

class OrderCreateView(CreateView):
    model = Order
    fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city', 'phone_number']
    template_name = 'orders/order_create.html'
    success_url = reverse_lazy('core:home')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            # We don't have first/last name on User model by default in some setups, but usually they exist.
            # Profiles were added earlier with phone and address.
            initial['first_name'] = self.request.user.first_name
            initial['last_name'] = self.request.user.last_name
            initial['email'] = self.request.user.email
            if hasattr(self.request.user, 'profile'):
                initial['address'] = self.request.user.profile.address
                initial['city'] = self.request.user.profile.city
                initial['phone_number'] = self.request.user.profile.phone
        return initial

    def form_valid(self, form):
        cart = Cart(self.request)
        if not list(cart):
            from django.contrib import messages
            messages.error(self.request, 'Your cart is empty.')
            return redirect('orders:cart_detail')

        order = form.save(commit=False)
        if self.request.user.is_authenticated:
            order.user = self.request.user
        else:
            order.user = None
        order.paid = False
        order.status = 'pending'
        order.save()
        for item in cart:
            product = item['product']
            OrderItem.objects.create(
                order=order,
                product=product,
                vendor=getattr(product, 'vendor', None),
                price=item['price'],
                quantity=item['quantity'],
            )
        if self.request.user.is_authenticated:
            if getattr(cart, 'applied_points', 0) > 0:
                RewardPoint.objects.create(
                    user=self.request.user,
                    points=-cart.applied_points,
                    transaction_type='redeemed',
                    order_reference=str(order.id)
                )
        else:
            if not self.request.session.session_key:
                self.request.session.create()
            remember_guest_order(self.request, order)

        cart.clear()
        from django.contrib import messages
        messages.info(self.request, 'Order created. Please complete payment to confirm.')
        return redirect('integrations:payment_checkout', order_id=order.id)

class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
class OrderDetailView(View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not user_can_access_order(request, order):
            from django.contrib import messages
            messages.error(request, 'You need to sign in to view this order, or checkout again from this device.')
            return redirect('accounts:login')
        return render(request, 'orders/order_detail.html', {'order': order})
