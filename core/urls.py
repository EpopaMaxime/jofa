from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    
    # Team
    path('team/', views.TeamListView.as_view(), name='team_list'),
    path('team/<slug:slug>/', views.TeamDetailView.as_view(), name='team_detail'),
    
    # News & Events
    path('news-events/', views.NewsEventListView.as_view(), name='news_event_list'),
    path('news-events/<slug:slug>/', views.NewsEventDetailView.as_view(), name='news_event_detail'),
]
