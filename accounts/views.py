from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, TemplateView, DetailView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from .forms import UserUpdateForm, ProfileUpdateForm, CustomRegistrationForm
from rewards.utils import get_user_points

class SignUpView(CreateView):
    form_class = CustomRegistrationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

class UserLoginView(LoginView):
    template_name = 'accounts/login.html'

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.profile
        # Check if orders exists (related name might be different or not defined)
        if hasattr(self.request.user, 'orders'):
            context['orders'] = self.request.user.orders.all()
        # Add available points
        context['available_points'] = get_user_points(self.request.user)
        return context

@login_required
def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'accounts/profile_edit.html', context)
