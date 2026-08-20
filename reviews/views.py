from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Review
from products.models import Product
from django.contrib import messages

class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        return Review.objects.filter(approved=True).select_related('user', 'product')

class ReviewCreateView(LoginRequiredMixin, View):
    def post(self, request, product_id=None):
        product = None
        if product_id:
            product = get_object_or_404(Product, id=product_id)
        
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        location = request.POST.get('location', '')
        
        if rating and comment:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment,
                location=location
            )
            messages.success(request, "Thank you for your essence review! It means the world to us.")
        else:
            messages.error(request, "Please provide both a rating and a comment.")

        if product:
            return redirect('products:product_detail', slug=product.slug)
        return redirect('reviews:review_list')
