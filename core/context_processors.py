"""
Context processors for ANNA platform.
"""
from django.contrib.auth.decorators import login_required


def navigation_context(request):
    """
    Context processor to add navigation context to all templates.
    """
    if not request.user.is_authenticated:
        return {
            'wakalas': [],
            'mchezo_groups': [],
            'has_wakala_access': False,
            'has_mchezo_access': False,
        }
    
    from core.models import WakalaRole, MchezoRole
    
    wakala_roles = WakalaRole.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('wakala')
    
    wakalas = [role.wakala for role in wakala_roles]
    
    mchezo_roles = MchezoRole.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('group')
    
    mchezo_groups = [role.group for role in mchezo_roles]
    
    return {
        'wakalas': wakalas,
        'mchezo_groups': mchezo_groups,
        'has_wakala_access': len(wakalas) > 0,
        'has_mchezo_access': len(mchezo_groups) > 0,
    }
