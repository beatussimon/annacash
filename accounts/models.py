"""
Custom User model for ANNA financial platform.

This model provides a single global User identity with contextual roles
scoped to different domains (Wakala, Mchezo).
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with contextual roles.
    
    Core identity is global. Roles are app-scoped and assigned per domain.
    """
    # Core identity fields
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Tracking
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Profile
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    # Tanzania-specific fields
    national_id = models.CharField(max_length=20, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return short name."""
        return self.first_name
    
    @property
    def is_wakala_owner(self):
        """Check if user owns any wakala business."""
        return self.wakala_owned.filter(is_active=True).exists()
    
    @property
    def is_mchezo_admin(self):
        """Check if user administers any mchezo groups."""
        return self.mchezo_admin.filter(is_active=True).exists()


class UserProfile(models.Model):
    """
    Extended user profile with preferences.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Preferences
    default_currency = models.CharField(max_length=3, default='TZS')
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')
    language = models.CharField(max_length=10, default='sw')  # Swahili default
    
    # Notification preferences
    sms_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    
    # UI preferences
    dashboard_layout = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"
