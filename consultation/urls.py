from django.urls import path
from . import views

app_name = 'consultation'

urlpatterns = [
    path('', views.ConsultationLandingView.as_view(), name='landing'),
    path('start/', views.ConsultationStartView.as_view(), name='start'),
    path('history/', views.ConsultationHistoryView.as_view(), name='history'),
    path('<uuid:public_id>/upload/', views.ConsultationUploadView.as_view(), name='upload'),
    path('<uuid:public_id>/results/', views.ConsultationResultsView.as_view(), name='results'),
    path('<uuid:public_id>/add-to-cart/', views.AddRecommendationsToCartView.as_view(), name='add_to_cart'),
]
