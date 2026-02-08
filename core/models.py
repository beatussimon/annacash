"""
Core models for ANNA financial platform.

This module contains base models with audit fields that all domain models
should inherit from. It also contains app-scoped role models.
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def deleted(self):
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteModel(models.Model):
    """Base model with soft delete support."""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='%(class)s_deleted'
    )
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, hard_delete=False):
        """Soft delete by default."""
        if hard_delete:
            return super().delete(using=using, keep_parents=keep_parents)
        
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()


class AuditModel(models.Model):
    """
    Base model with comprehensive audit fields.
    
    Every financial transaction must be:
    - Entered manually by a logged-in user
    - Timestamped precisely
    - Attributed to the exact user who recorded it
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        editable=False
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_updated',
        blank=True,
        null=True,
        editable=False
    )
    # For tracking the original recorder of a financial transaction
    original_recorder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_recorded',
        editable=False,
        help_text="The user who originally recorded this transaction"
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Override save to set audit fields."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Set created_by on first save
        if not self.pk and not kwargs.get('force_insert'):
            pass  # Will be handled by the view
        
        super().save(*args, **kwargs)


class AuditableModel(AuditModel, SoftDeleteModel):
    """
    Base model combining audit and soft delete functionality.
    
    All domain models should inherit from this.
    """
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True


# =============================================================================
# CONTEXTUAL ROLES - App-Scoped Permissions
# =============================================================================

class WakalaRole(models.Model):
    """
    Wakala-specific roles scoped to individual wakala businesses.
    
    Wakala roles:
    - Owner: Full control over the wakala business
    - Manager: Day-to-day operations, can open/close days
    - Agent: Can record transactions within approved limits
    """
    WAKALA_ROLES = [
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('agent', 'Agent'),
    ]
    
    wakala = models.ForeignKey(
        'wakala.Wakala',
        on_delete=models.CASCADE,
        related_name='roles'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wakala_roles'
    )
    role = models.CharField(max_length=20, choices=WAKALA_ROLES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='wakala_roles_granted'
    )
    
    class Meta:
        unique_together = ('wakala', 'user')
        verbose_name = 'Wakala Role'
        verbose_name_plural = 'Wakala Roles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} ({self.wakala.name})"


class MchezoRole(models.Model):
    """
    Mchezo-specific roles scoped to individual groups.
    
    Mchezo roles:
    - Group Admin: Full control over the group
    - Treasurer: Can record contributions and payouts
    - Member: Can view and make contributions
    - Viewer: Read-only access
    """
    MCHEZO_ROLES = [
        ('admin', 'Group Admin'),
        ('treasurer', 'Treasurer'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    
    group = models.ForeignKey(
        'mchezo.Group',
        on_delete=models.CASCADE,
        related_name='roles'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mchezo_roles'
    )
    role = models.CharField(max_length=20, choices=MCHEZO_ROLES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mchezo_roles_granted'
    )
    
    class Meta:
        unique_together = ('group', 'user')
        verbose_name = 'Mchezo Role'
        verbose_name_plural = 'Mchezo Roles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} ({self.group.name})"


# =============================================================================
# AUDIT LOG
# =============================================================================

class AuditLog(models.Model):
    """
    Comprehensive audit log for all critical actions.
    
    This is a separate table for performance and to avoid
    interfering with domain model operations.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('open_day', 'Open Financial Day'),
        ('close_day', 'Close Financial Day'),
        ('record_transaction', 'Record Transaction'),
        ('adjust_balance', 'Balance Adjustment'),
        ('payout', 'Payout'),
        ('contribution', 'Contribution'),
        ('role_change', 'Role Change'),
        ('export', 'Export'),
        ('other', 'Other'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Details
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    description = models.TextField()
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action', 'timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
