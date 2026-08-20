from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.ReviewListView.as_view(), name='review_list'),
    path('add/', views.ReviewCreateView.as_view(), name='review_add_general'),
    path('add/<int:product_id>/', views.ReviewCreateView.as_view(), name='review_add'),
]
