"""
Forms for accounts app.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm

from core.forms import FormStyleMixin
from .models import UserProfile

User = get_user_model()


class UserCreationForm(FormStyleMixin, BaseUserCreationForm):
    """Custom user creation form."""

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name", "phone_number")


class UserChangeForm(FormStyleMixin, BaseUserChangeForm):
    """Custom user change form."""

    class Meta(BaseUserChangeForm.Meta):
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "is_active",
            "is_staff",
            "is_superuser",
        )


class UserProfileForm(FormStyleMixin, forms.ModelForm):
    """Form for user profile."""

    class Meta:
        model = UserProfile
        fields = (
            "default_currency",
            "date_format",
            "language",
            "sms_notifications",
            "email_notifications",
        )


class UserRegistrationForm(FormStyleMixin, forms.ModelForm):
    """Registration form for new users."""

    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ("email", "phone_number", "first_name", "last_name")

    def clean_password_confirm(self):
        """Check that passwords match."""
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match")
        return password_confirm

    def clean_email(self):
        """Check that email is not already in use."""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered")
        return email
