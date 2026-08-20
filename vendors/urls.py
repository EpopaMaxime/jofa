from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.VendorLandingView.as_view(), name='landing'),
    path('register/', views.VendorRegisterView.as_view(), name='register'),
    path('open-store/', views.VendorOpenStoreView.as_view(), name='open_store'),
    path('pending/', views.VendorPendingView.as_view(), name='pending'),
    path('suspended/', views.VendorSuspendedView.as_view(), name='suspended'),
    path('directory/', views.VendorDirectoryView.as_view(), name='directory'),
    path('dashboard/', views.VendorDashboardView.as_view(), name='dashboard'),
    path('dashboard/products/', views.VendorProductListView.as_view(), name='product_list'),
    path('dashboard/products/add/', views.VendorProductCreateView.as_view(), name='product_add'),
    path(
        'dashboard/products/<int:pk>/edit/',
        views.VendorProductUpdateView.as_view(),
        name='product_edit',
    ),
    path(
        'dashboard/products/<int:pk>/delete/',
        views.VendorProductDeleteView.as_view(),
        name='product_delete',
    ),
    path('dashboard/orders/', views.VendorOrderListView.as_view(), name='orders'),
    path(
        'dashboard/orders/<int:pk>/status/',
        views.VendorOrderItemUpdateView.as_view(),
        name='order_status',
    ),
    path('dashboard/profile/', views.VendorProfileUpdateView.as_view(), name='profile_edit'),
    path('store/<slug:slug>/', views.VendorStorefrontView.as_view(), name='storefront'),
]
