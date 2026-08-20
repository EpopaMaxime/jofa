from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.CartDetailView.as_view(), name='cart_detail'),
    path('cart/add/<int:product_id>/', views.CartAddView.as_view(), name='cart_add'),
    path('cart/remove/<int:product_id>/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('cart/coupon/apply/', views.CouponApplyView.as_view(), name='coupon_apply'),
    path('cart/points/apply/', views.RedeemPointsView.as_view(), name='points_apply'),
    path('checkout/', views.OrderCreateView.as_view(), name='order_create'),
    path('history/', views.OrderHistoryView.as_view(), name='order_history'),
    path('receipt/<int:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
]
