from django.urls import path
from . import views

app_name = 'rewards'

urlpatterns = [
    path('loyalty/', views.loyalty_program, name='loyalty_program'),
]
