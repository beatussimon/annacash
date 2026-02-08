"""
Mchezo domain models for ANNA financial platform.

This module contains all models for managing mchezo (rotating savings / ROSCA)
including groups, cycles, memberships, contributions, and payouts.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

from core.models import AuditableModel


class Group(AuditableModel):
    """
    A mchezo (rotating savings) group.
    
    Groups are social financial circles where members contribute
    regularly and take turns receiving the pooled amount.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Group settings
    contribution_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(100)]
    )
    contribution_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('biweekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
        ],
        default='weekly'
    )
    max_members = models.PositiveIntegerField(default=10)
    
    # Scheduling
    contribution_day = models.PositiveIntegerField(
        help_text="Day of week (1=Monday, 7=Sunday) or day of month",
        default=1
    )
    contribution_time = models.TimeField(default=timezone.now)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_open = models.BooleanField(
        default=True,
        help_text="Allow new members to join"
    )
    
    # Payout configuration
    payout_order_method = models.CharField(
        max_length=30,
        choices=[
            ('random', 'Random'),
            ('fixed', 'Fixed (members choose)'),
            ('bidding', 'Bidding (highest bidder wins)'),
            ('sequential', 'Sequential (first come, first served)'),
        ],
        default='random'
    )
    
    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_current_cycle(self):
        """Get the currently active cycle."""
        return self.cycles.filter(status='active').first()
    
    def get_member_count(self):
        """Get the number of active members."""
        return self.memberships.filter(status='active', is_deleted=False).count()
    
    def is_full(self):
        """Check if group is at max capacity."""
        return self.get_member_count() >= self.max_members


class Membership(AuditableModel):
    """
    Membership in a mchezo group.
    
    Links a user to a group with their role and position.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
        ('defaulted', 'Defaulted'),
    ]
    
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mchezo_memberships'
    )
    
    # Membership details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    join_date = models.DateField(default=timezone.now)
    exit_date = models.DateField(blank=True, null=True)
    
    # Position in payout order
    payout_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Position in payout order (1=first payout)"
    )
    
    # Contact for group communications
    phone_number = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    class Meta:
        unique_together = ('group', 'user')
        ordering = ['payout_order']
        verbose_name = 'Membership'
        verbose_name_plural = 'Memberships'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.group.name}"
    
    def is_active(self):
        """Check if membership is active."""
        return self.status == 'active'


class Cycle(AuditableModel):
    """
    A single cycle of a mchezo group.
    
    A cycle runs from the first contribution until all members
    have received their payout.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='cycles'
    )
    
    cycle_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    
    # Payout tracking
    payouts_made = models.PositiveIntegerField(default=0)
    total_payouts = models.PositiveIntegerField(
        default=0,
        help_text="Total amount paid out this cycle"
    )
    
    # Settings
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('group', 'cycle_number')
        ordering = ['-cycle_number']
        verbose_name = 'Cycle'
        verbose_name_plural = 'Cycles'
    
    def __str__(self):
        return f"{self.group.name} - Cycle {self.cycle_number}"
    
    def start_cycle(self):
        """Start this cycle."""
        if self.status != 'draft':
            raise ValueError("Only draft cycles can be started")
        self.status = 'active'
        self.start_date = timezone.now().date()
        self.save()
        return self
    
    def complete_cycle(self):
        """Complete this cycle."""
        if self.status != 'active':
            raise ValueError("Only active cycles can be completed")
        self.status = 'completed'
        self.end_date = timezone.now().date()
        self.save()
        return self
    
    def get_contribution_progress(self):
        """Get contribution progress for this cycle."""
        total_expected = self.group.memberships.filter(
            status='active'
        ).count()
        contributions = self.contributions.filter(
            status='completed'
        ).count()
        return {
            'total': total_expected,
            'made': contributions,
            'remaining': total_expected - contributions
        }
    
    def is_complete(self):
        """Check if cycle is complete."""
        if self.status != 'active':
            return True
        return self.payouts_made >= self.group.memberships.filter(
            status='active'
        ).count()


class Contribution(AuditableModel):
    """
    A contribution made by a member in a cycle.
    
    All contributions must be recorded manually.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    cycle = models.ForeignKey(
        Cycle,
        on_delete=models.CASCADE,
        related_name='contributions'
    )
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name='contributions'
    )
    
    # Contribution details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField(max_length=3, default='TZS')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    # Timing
    contribution_date = models.DateField(default=timezone.now)
    contribution_time = models.TimeField(default=timezone.now)
    
    # Payment details
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['contribution_date', 'contribution_time']
        verbose_name = 'Contribution'
        verbose_name_plural = 'Contributions'
    
    def __str__(self):
        return f"{self.membership.user.get_full_name()} - {self.amount} ({self.cycle})"


class Payout(AuditableModel):
    """
    A payout to a member in a cycle.
    
    Each member receives exactly one payout per cycle.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    cycle = models.ForeignKey(
        Cycle,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    
    # Payout details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField(max_length=3, default='TZS')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timing
    scheduled_date = models.DateField()
    completed_date = models.DateField(blank=True, null=True)
    
    # Payment details
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Position
    payout_order = models.PositiveIntegerField(
        help_text="Order in which payout was received"
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('cycle', 'membership')
        ordering = ['payout_order']
        verbose_name = 'Payout'
        verbose_name_plural = 'Payouts'
    
    def __str__(self):
        return f"{self.membership.user.get_full_name()} - {self.amount} ({self.cycle})"
    
    def complete_payout(self):
        """Mark payout as completed."""
        self.status = 'completed'
        self.completed_date = timezone.now().date()
        self.save()
        return self
