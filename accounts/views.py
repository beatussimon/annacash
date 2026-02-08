"""
Views for accounts app.
"""
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.shortcuts import render, redirect
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User, UserProfile
from .forms import UserRegistrationForm, UserProfileForm


class CustomLoginView(LoginView):
    """Custom login view."""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Handle successful login."""
        login(self.request, form.get_user())
        messages.success(self.request, 'Welcome back!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle failed login."""
        messages.error(self.request, 'Invalid credentials. Please try again.')
        return super().form_invalid(form)


class UserRegistrationView(CreateView):
    """User registration view."""
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard:home')
    
    def form_valid(self, form):
        """Handle successful registration."""
        user = form.save()
        # Create user profile
        UserProfile.objects.create(user=user)
        # Log in the user
        login(self.request, user)
        messages.success(self.request, 'Registration successful! Welcome to ANNA.')
        return redirect(self.success_url)


class UserProfileView(LoginRequiredMixin, UpdateView):
    """User profile view."""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self, queryset=None):
        """Get the user's profile."""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_context_data(self, **kwargs):
        """Add user to context."""
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class UserListView(LoginRequiredMixin, ListView):
    """List all users (superuser only)."""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        """Only superusers can view all users."""
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


def logout_view(request):
    """Custom logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


def profile_redirect(request):
    """Redirect to the correct profile view."""
    return redirect('accounts:profile')
