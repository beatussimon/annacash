"""
Permission helpers for ANNA platform.

Provides contextual permission checking for Wakala and Mchezo domains.
"""
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps


def has_wakala_role(user, wakala, roles):
    """
    Check if user has any of the specified roles for a wakala.
    
    Args:
        user: The user to check
        wakala: The wakala instance
        roles: List of role names (e.g., ['owner', 'manager'])
    
    Returns:
        bool: True if user has any of the roles
    """
    from core.models import WakalaRole
    
    if user.is_superuser:
        return True
    
    return WakalaRole.objects.filter(
        user=user,
        wakala=wakala,
        role__in=roles,
        is_active=True
    ).exists()


def has_mchezo_role(user, group, roles):
    """
    Check if user has any of the specified roles for a mchezo group.
    
    Args:
        user: The user to check
        group: The mchezo group instance
        roles: List of role names (e.g., ['admin', 'treasurer'])
    
    Returns:
        bool: True if user has any of the roles
    """
    from core.models import MchezoRole
    
    if user.is_superuser:
        return True
    
    return MchezoRole.objects.filter(
        user=user,
        group=group,
        role__in=roles,
        is_active=True
    ).exists()


def wakala_owner_required(view_func):
    """Decorator to require wakala owner role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        wakala_id = kwargs.get('wakala_id')
        if not wakala_id:
            raise PermissionDenied("Wakala ID required")
        
        from wakala.models import Wakala
        try:
            wakala = Wakala.objects.get(pk=wakala_id)
        except Wakala.DoesNotExist:
            raise PermissionDenied("Wakala not found")
        
        if not has_wakala_role(request.user, wakala, ['owner']):
            raise PermissionDenied("You must be the owner of this wakala")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def wakala_manager_or_owner_required(view_func):
    """Decorator to require wakala manager or owner role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        wakala_id = kwargs.get('wakala_id')
        if not wakala_id:
            raise PermissionDenied("Wakala ID required")
        
        from wakala.models import Wakala
        try:
            wakala = Wakala.objects.get(pk=wakala_id)
        except Wakala.DoesNotExist:
            raise PermissionDenied("Wakala not found")
        
        if not has_wakala_role(request.user, wakala, ['owner', 'manager']):
            raise PermissionDenied("You must be owner or manager of this wakala")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def mchezo_admin_required(view_func):
    """Decorator to require mchezo admin role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        group_id = kwargs.get('group_id')
        if not group_id:
            raise PermissionDenied("Group ID required")
        
        from mchezo.models import Group
        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            raise PermissionDenied("Group not found")
        
        if not has_mchezo_role(request.user, group, ['admin']):
            raise PermissionDenied("You must be an admin of this group")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def mchezo_treasurer_or_admin_required(view_func):
    """Decorator to require mchezo treasurer or admin role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        group_id = kwargs.get('group_id')
        if not group_id:
            raise PermissionDenied("Group ID required")
        
        from mchezo.models import Group
        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            raise PermissionDenied("Group not found")
        
        if not has_mchezo_role(request.user, group, ['admin', 'treasurer']):
            raise PermissionDenied("You must be admin or treasurer of this group")
        
        return view_func(request, *args, **kwargs)
    return wrapper


class WakalaPermissionMixin:
    """
    Mixin to add wakala-specific permission checking to views.
    """
    
    def get_wakala(self):
        """Get the wakala instance."""
        wakala_id = self.kwargs.get('wakala_id')
        from wakala.models import Wakala
        return Wakala.objects.get(pk=wakala_id)
    
    def has_wakala_role(self, roles):
        """Check if user has required role for this wakala."""
        return has_wakala_role(self.request.user, self.get_wakala(), roles)
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions before dispatching."""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if not self.has_wakala_role(self.required_roles):
            raise PermissionDenied("Insufficient permissions for this wakala")
        
        return super().dispatch(request, *args, **kwargs)


class MchezoPermissionMixin:
    """
    Mixin to add mchezo-specific permission checking to views.
    """
    
    def get_group(self):
        """Get the group instance."""
        group_id = self.kwargs.get('group_id')
        from mchezo.models import Group
        return Group.objects.get(pk=group_id)
    
    def has_mchezo_role(self, roles):
        """Check if user has required role for this group."""
        return has_mchezo_role(self.request.user, self.get_group(), roles)
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions before dispatching."""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if not self.has_mchezo_role(self.required_roles):
            raise PermissionDenied("Insufficient permissions for this group")
        
        return super().dispatch(request, *args, **kwargs)
