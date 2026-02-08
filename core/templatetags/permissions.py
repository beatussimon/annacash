"""
Permission template tags for ANNA platform.

Provides conditional rendering based on user roles and permissions.
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


# =============================================================================
# SIMPLE TAGS
# =============================================================================

@register.simple_tag
def get_user_role_for_wakala(user, wakala):
    """
    Get user's role for a specific wakala.
    
    Usage: {% get_user_role_for_wakala user wakala as role %}
    """
    if user.is_superuser:
        return 'superuser'
    
    from core.models import WakalaRole
    role = WakalaRole.objects.filter(
        user=user,
        wakala=wakala,
        is_active=True
    ).first()
    
    return role.role if role else None


@register.simple_tag
def get_user_role_for_mchezo(user, group):
    """
    Get user's role for a specific mchezo group.
    
    Usage: {% get_user_role_for_mchezo user group as role %}
    """
    if user.is_superuser:
        return 'superuser'
    
    from core.models import MchezoRole
    role = MchezoRole.objects.filter(
        user=user,
        group=group,
        is_active=True
    ).first()
    
    return role.role if role else None


@register.simple_tag
def can_record_transaction(user, wakala):
    """Check if user can record transactions."""
    if user.is_superuser:
        return True
    from core.permissions import has_wakala_role
    return has_wakala_role(user, wakala, ['owner', 'manager', 'agent'])


@register.simple_tag
def can_edit_transaction(user, transaction):
    """Check if user can edit a transaction."""
    if user.is_superuser:
        return True
    if not transaction.is_editable():
        return False
    from core.permissions import has_wakala_role
    return has_wakala_role(user, transaction.wakala, ['owner', 'manager'])


@register.simple_tag
def can_delete_transaction(user, transaction):
    """Check if user can delete a transaction."""
    if user.is_superuser:
        return True
    if not transaction.is_deletable():
        return False
    from core.permissions import has_wakala_role
    return has_wakala_role(user, transaction.wakala, ['owner'])


@register.simple_tag
def can_close_financial_day(user, financial_day):
    """Check if user can close a financial day."""
    if user.is_superuser:
        return True
    if financial_day.status != 'open':
        return False
    from core.permissions import has_wakala_role
    return has_wakala_role(user, financial_day.wakala, ['owner', 'manager'])


@register.simple_tag
def can_open_financial_day(user, wakala):
    """Check if user can open a financial day."""
    if user.is_superuser:
        return True
    if not wakala.can_open_new_day():
        return False
    from core.permissions import has_wakala_role
    return has_wakala_role(user, wakala, ['owner', 'manager', 'agent'])


@register.simple_tag
def can_resolve_discrepancy(user, financial_day):
    """Check if user can resolve discrepancies."""
    if user.is_superuser:
        return True
    if financial_day.status != 'open':
        return False
    from core.permissions import has_wakala_role
    return has_wakala_role(user, financial_day.wakala, ['owner', 'manager'])


@register.simple_tag
def can_manage_wakala(user, wakala):
    """Check if user can manage wakala settings."""
    if user.is_superuser:
        return True
    from core.permissions import has_wakala_role
    return has_wakala_role(user, wakala, ['owner'])


@register.simple_tag
def can_view_cross_wakala(user):
    """Check if user can view cross-wakala analytics."""
    return user.is_superuser


@register.simple_tag
def can_record_contribution(user, group):
    """Check if user can record contributions."""
    if user.is_superuser:
        return True
    from core.permissions import has_mchezo_role
    return has_mchezo_role(user, group, ['admin', 'treasurer'])


@register.simple_tag
def can_record_payout(user, group):
    """Check if user can record payouts."""
    if user.is_superuser:
        return True
    from core.permissions import has_mchezo_role
    return has_mchezo_role(user, group, ['admin', 'treasurer'])


@register.simple_tag
def can_manage_members(user, group):
    """Check if user can manage group members."""
    if user.is_superuser:
        return True
    from core.permissions import has_mchezo_role
    return has_mchezo_role(user, group, ['admin'])


@register.simple_tag
def can_close_cycle(user, group):
    """Check if user can close group cycle."""
    if user.is_superuser:
        return True
    from core.permissions import has_mchezo_role
    return has_mchezo_role(user, group, ['admin'])


@register.simple_tag
def can_export_group_data(user, group):
    """Check if user can export group data."""
    if user.is_superuser:
        return True
    from core.permissions import has_mchezo_role
    role = get_user_role_for_mchezo(user, group)
    return role in ['admin', 'treasurer']


@register.simple_tag
def get_role_display_name(role):
    """Get display name for a role."""
    role_names = {
        'superuser': 'Superadmin',
        'owner': 'Owner',
        'manager': 'Manager',
        'agent': 'Agent',
        'admin': 'Group Admin',
        'treasurer': 'Treasurer',
        'member': 'Member',
        'viewer': 'Viewer',
    }
    return role_names.get(role, role.title())


@register.simple_tag
def get_role_icon(role):
    """Get icon class for a role."""
    role_icons = {
        'superuser': 'bi-shield-check',
        'owner': 'bi-star',
        'manager': 'bi-person-check',
        'agent': 'bi-person',
        'admin': 'bi-gear',
        'treasurer': 'bi-cash-coin',
        'member': 'bi-people',
        'viewer': 'bi-eye',
    }
    return role_icons.get(role, 'bi-circle')


@register.simple_tag
def get_role_badge_class(role):
    """Get Bootstrap badge class for a role."""
    role_badges = {
        'superuser': 'bg-danger',
        'owner': 'bg-primary',
        'manager': 'bg-success',
        'agent': 'bg-info',
        'admin': 'bg-warning',
        'treasurer': 'bg-success',
        'member': 'bg-secondary',
        'viewer': 'bg-light text-dark',
    }
    return role_badges.get(role, 'bg-secondary')


@register.simple_tag
def format_tzs(amount):
    """Format amount as TZS."""
    try:
        return f"TZS {float(amount):,.0f}"
    except (ValueError, TypeError):
        return "TZS 0"


# =============================================================================
# FILTER-STYLE TAGS (for use in if conditions)
# =============================================================================

@register.filter
def can_record_transaction(user, wakala):
    """Filter: Check if user can record transactions."""
    return can_record_transaction(user, wakala)


@register.filter
def can_edit_transaction(user, transaction):
    """Filter: Check if user can edit a transaction."""
    return can_edit_transaction(user, transaction)


@register.filter
def can_delete_transaction(user, transaction):
    """Filter: Check if user can delete a transaction."""
    return can_delete_transaction(user, transaction)


@register.filter
def can_close_financial_day(user, financial_day):
    """Filter: Check if user can close a financial day."""
    return can_close_financial_day(user, financial_day)


@register.filter
def can_open_financial_day(user, wakala):
    """Filter: Check if user can open a financial day."""
    return can_open_financial_day(user, wakala)


@register.filter
def can_resolve_discrepancy(user, financial_day):
    """Filter: Check if user can resolve discrepancies."""
    return can_resolve_discrepancy(user, financial_day)


@register.filter
def can_manage_wakala(user, wakala):
    """Filter: Check if user can manage wakala settings."""
    return can_manage_wakala(user, wakala)


@register.filter
def can_record_contribution(user, group):
    """Filter: Check if user can record contributions."""
    return can_record_contribution(user, group)


@register.filter
def can_record_payout(user, group):
    """Filter: Check if user can record payouts."""
    return can_record_payout(user, group)


@register.filter
def can_manage_members(user, group):
    """Filter: Check if user can manage group members."""
    return can_manage_members(user, group)


@register.filter
def can_close_cycle(user, group):
    """Filter: Check if user can close group cycle."""
    return can_close_cycle(user, group)


# =============================================================================
# INCLUSION TAGS
# =============================================================================

@register.inclusion_tag('components/role_badge.html')
def render_role_badge(role):
    """Render a role badge with icon and name."""
    return {
        'role': role,
        'display_name': get_role_display_name(role),
        'icon': get_role_icon(role),
        'badge_class': get_role_badge_class(role),
    }


@register.inclusion_tag('components/permission_denied.html')
def render_permission_denied(action):
    """Render a permission denied message."""
    return {
        'action': action,
    }
