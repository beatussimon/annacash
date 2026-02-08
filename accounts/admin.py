"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserCreationForm, UserChangeForm
from .models import UserProfile

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    """Custom user admin."""
    form = UserChangeForm
    add_form = UserCreationForm
    
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 
                    'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number',
                                     'national_id', 'region', 'district')}),
        ('Profile', {'fields': ('profile_image', 'bio')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                   'groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number',
                      'password1', 'password2'),
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make date_joined readonly for existing users."""
        if obj:
            return ('date_joined', 'last_login')
        return ()


class UserProfileAdmin(admin.ModelAdmin):
    """User profile admin."""
    list_display = ('user', 'default_currency', 'language', 
                   'sms_notifications', 'email_notifications')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
