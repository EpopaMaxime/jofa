from django.views.generic import TemplateView, CreateView, ListView, DetailView
from .models import FAQ, Partner, ContactMessage, TeamMember, NewsEvent
from products.models import Product
from blog.models import Post
from reviews.models import Review
from django.urls import reverse_lazy

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['featured_products'] removed as requested
        context['latest_arrivals'] = Product.objects.filter(available=True).order_by('-created_at')[:9]
        context['latest_posts'] = Post.objects.filter(published=True)[:3]
        context['reviews'] = Review.objects.filter(approved=True)[:6]
        context['faqs'] = FAQ.objects.all().order_by('-id')[:4]
        return context

class TeamListView(ListView):
    model = TeamMember
    template_name = 'core/team_list.html'
    context_object_name = 'members'

class TeamDetailView(DetailView):
    model = TeamMember
    template_name = 'core/team_detail.html'
    context_object_name = 'member'

class NewsEventListView(ListView):
    model = NewsEvent
    template_name = 'core/news_event_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        queryset = NewsEvent.objects.filter(is_published=True)
        type_filter = self.request.GET.get('type')
        if type_filter in ['news', 'event']:
            queryset = queryset.filter(type=type_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_type'] = self.request.GET.get('type', 'all')
        return context

class NewsEventDetailView(DetailView):
    model = NewsEvent
    template_name = 'core/news_event_detail.html'
    context_object_name = 'item'

class AboutView(TemplateView):
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Team members removed as per request to have dedicated page
        context['partners'] = Partner.objects.all()
        return context

class FAQView(ListView):
    model = FAQ
    template_name = 'core/faq.html'
    context_object_name = 'faqs'

class ContactView(CreateView):
    model = ContactMessage
    fields = ['name', 'email', 'phone', 'subject', 'message']
    template_name = 'core/contact.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        message = form.save()
        try:
            from .utils import send_contact_notification
            send_contact_notification(message, self.request)
            from django.contrib import messages
            messages.success(self.request, "Your message has been sent successfully!")
        except Exception as e:
            print(f"Error sending contact email: {e}")
            from django.contrib import messages
            messages.success(self.request, "Your message has been recorded.")
        return super().form_valid(form)
