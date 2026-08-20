from django.urls import path
from . import views, api

app_name = 'integrations'

urlpatterns = [
    path('pay/<int:order_id>/', views.PaymentCheckoutView.as_view(), name='payment_checkout'),
    path('pay/<int:order_id>/confirm/', views.PaymentConfirmView.as_view(), name='payment_confirm'),
    path('pay/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('pay/<int:order_id>/cancel/', views.PaymentCancelView.as_view(), name='payment_cancel'),
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
    # Public JSON APIs for future expansion
    path('api/concerns/', api.ConcernsAPIView.as_view(), name='api_concerns'),
    path('api/recommend/', api.RecommendAPIView.as_view(), name='api_recommend'),
    path('api/providers/', api.ProvidersAPIView.as_view(), name='api_providers'),
]
