from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    
    # Team removed as it is now in About page, but detail view is kept for interactivity
    path('team/<slug:slug>/', views.TeamDetailView.as_view(), name='team_detail'),
    
    # News & Events
    path('news-events/', views.NewsEventListView.as_view(), name='news_event_list'),
    path('news-events/<slug:slug>/', views.NewsEventDetailView.as_view(), name='news_event_detail'),
]
