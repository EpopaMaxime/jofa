from django.urls import path
from . import views
from . import wishlist_views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('wishlist/', wishlist_views.wishlist_detail, name='wishlist_detail'),
    path('wishlist/add/<int:product_id>/', wishlist_views.wishlist_add, name='wishlist_add'),
    path('wishlist/remove/<int:product_id>/', wishlist_views.wishlist_remove, name='wishlist_remove'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
