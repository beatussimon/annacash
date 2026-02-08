"""
Mchezo cycle management service for ANNA platform.

Implements the rotating savings cycle logic with automatic
payout tracking and cycle completion.
"""
from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models import Max
from django.utils import timezone


class MchezoService:
    """
    Service for managing mchezo (rotating savings) groups and cycles.
    """
    
    @staticmethod
    @db_transaction.atomic
    def create_group(admin_user, **group_data):
        """
        Create a new mchezo group.
        
        Args:
            admin_user: The user creating the group (becomes admin)
            **group_data: Group configuration
            
        Returns:
            Group: The created group
        """
        from mchezo.models import Group, Membership
        from core.models import MchezoRole
        
        group = Group.objects.create(**group_data)
        
        # Create admin membership
        membership = Membership.objects.create(
            group=group,
            user=admin_user,
            status='active',
            join_date=timezone.now().date(),
            payout_order=1
        )
        
        # Create admin role
        MchezoRole.objects.create(
            group=group,
            user=admin_user,
            role='admin',
            granted_by=admin_user
        )
        
        return group
    
    @staticmethod
    @db_transaction.atomic
    def add_member(group, user, payout_order=None, phone_number=None, created_by=None):
        """
        Add a member to a group.
        
        Args:
            group: The mchezo group
            user: The user to add
            payout_order: Optional payout order position
            phone_number: Optional phone number
            created_by: The user creating the membership (for audit)
            
        Returns:
            Membership: The created membership
        """
        from mchezo.models import Membership
        from core.models import MchezoRole
        
        if group.is_full():
            raise ValueError("Group is at maximum capacity")
        
        if not group.is_open:
            raise ValueError("Group is not open for new members")
        
        # Get next payout order if not specified
        if payout_order is None:
            current_max = Membership.objects.filter(
                group=group,
                status='active'
            ).aggregate(max_order=Max('payout_order'))['max_order'] or 0
            payout_order = current_max + 1
        
        membership = Membership.objects.create(
            group=group,
            user=user,
            status='active',
            join_date=timezone.now().date(),
            payout_order=payout_order,
            phone_number=phone_number or user.phone_number or '',
            created_by=created_by or group.created_by,
            original_recorder=created_by or group.created_by
        )
        
        MchezoRole.objects.create(
            group=group,
            user=user,
            role='member',
            granted_by=created_by or group.created_by
        )
        
        return membership
    
    @staticmethod
    @db_transaction.atomic
    def start_cycle(group, created_by=None):
        """
        Start a new cycle for a group.
        
        Args:
            group: The mchezo group
            created_by: The user starting the cycle (for audit)
            
        Returns:
            Cycle: The started cycle
        """
        from mchezo.models import Cycle
        
        # Check for existing active cycle
        if group.get_current_cycle():
            raise ValueError("An active cycle already exists")
        
        # Get next cycle number
        last_cycle = group.cycles.order_by('-cycle_number').first()
        next_number = (last_cycle.cycle_number + 1) if last_cycle else 1
        
        # Create and start the cycle
        cycle = Cycle.objects.create(
            group=group,
            cycle_number=next_number,
            status='active',
            start_date=timezone.now().date(),
            created_by=created_by or group.created_by,
            original_recorder=created_by or group.created_by,
        )
        
        return cycle
    
    @staticmethod
    @db_transaction.atomic
    def record_contribution(cycle, membership, amount, payment_method, created_by=None, **kwargs):
        """
        Record a contribution for a member.
        
        Args:
            cycle: The active cycle
            membership: The member's membership
            amount: Contribution amount
            payment_method: Payment method
            created_by: The user recording the contribution (for audit)
            **kwargs: Additional details (including contribution_week)
            
        Returns:
            Contribution: The created contribution
        """
        from mchezo.models import Contribution
        
        contribution_week = kwargs.pop('contribution_week', cycle.get_current_week())
        
        contribution = Contribution.objects.create(
            cycle=cycle,
            membership=membership,
            amount=amount,
            contribution_week=contribution_week,
            payment_method=payment_method,
            status='completed',
            contribution_date=timezone.now().date(),
            contribution_time=timezone.now().time(),
            created_by=created_by or cycle.created_by,
            original_recorder=created_by or cycle.created_by,
            **kwargs
        )
        
        return contribution
    
    @staticmethod
    @db_transaction.atomic
    def record_bulk_contribution(cycle, membership, amount_per_week, weeks_count, payment_method, created_by=None, **kwargs):
        """
        Record bulk contributions for multiple weeks at once.
        
        Args:
            cycle: The active cycle
            membership: The member's membership
            amount_per_week: Amount to pay per week
            weeks_count: Number of weeks to pay for
            payment_method: Payment method
            created_by: The user recording the contribution (for audit)
            **kwargs: Additional details
            
        Returns:
            list: List of created Contribution objects
        """
        from mchezo.models import Contribution
        
        contributions = []
        current_week = cycle.get_current_week()
        total_weeks = cycle.group.get_member_count()
        
        for i in range(int(weeks_count)):
            week_num = current_week + i
            if week_num > total_weeks:
                break
            
            contribution = Contribution.objects.create(
                cycle=cycle,
                membership=membership,
                amount=amount_per_week,
                contribution_week=week_num,
                payment_method=payment_method,
                status='completed',
                contribution_date=timezone.now().date(),
                contribution_time=timezone.now().time(),
                created_by=created_by or cycle.created_by,
                original_recorder=created_by or cycle.created_by,
                **kwargs
            )
            contributions.append(contribution)
        
        return contributions
    
    @staticmethod
    @db_transaction.atomic
    def record_payout(cycle, membership, amount, payment_method, created_by=None, **kwargs):
        """
        Record a payout for a member.
        
        Args:
            cycle: The active cycle
            membership: The member receiving payout
            amount: Payout amount
            payment_method: Payment method
            created_by: The user recording the payout (for audit)
            **kwargs: Additional details
            
        Returns:
            Payout: The created payout
        """
        from mchezo.models import Payout
        
        # Get payout order
        payouts_count = cycle.payouts.count()
        payout_order = payouts_count + 1
        
        payout = Payout.objects.create(
            cycle=cycle,
            membership=membership,
            amount=amount,
            payment_method=payment_method,
            status='completed',
            scheduled_date=timezone.now().date(),
            completed_date=timezone.now().date(),
            payout_order=payout_order,
            created_by=created_by or cycle.created_by,
            original_recorder=created_by or cycle.created_by,
            **kwargs
        )
        
        # Update cycle stats
        cycle.payouts_made = payout_order
        cycle.total_payouts += amount
        cycle.save()
        
        # Check if cycle is complete
        if cycle.is_complete():
            MchezoService.complete_cycle(cycle)
        
        return payout
    
    @staticmethod
    @db_transaction.atomic
    def complete_cycle(cycle, updated_by=None):
        """
        Complete a cycle.
        
        Args:
            cycle: The cycle to complete
            updated_by: The user completing the cycle (for audit)
        """
        from mchezo.models import Cycle
        
        cycle.status = 'completed'
        cycle.end_date = timezone.now().date()
        cycle.updated_by = updated_by or cycle.created_by
        cycle.save()
    
    @staticmethod
    def get_cycle_progress(cycle):
        """
        Get progress information for a cycle.
        
        Args:
            cycle: The cycle to check
            
        Returns:
            dict: Progress information
        """
        from django.db.models import Sum
        
        total_members = cycle.group.memberships.filter(status='active').count()
        payouts_made = cycle.payouts.filter(status='completed').count()
        
        contributions_total = cycle.contributions.filter(
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        payouts_total = cycle.payouts.filter(
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        return {
            'cycle_number': cycle.cycle_number,
            'status': cycle.status,
            'total_members': total_members,
            'payouts_made': payouts_made,
            'payouts_remaining': total_members - payouts_made,
            'contributions_total': contributions_total,
            'payouts_total': payouts_total,
            'is_complete': cycle.is_complete(),
            'progress_percent': (payouts_made / total_members * 100) if total_members > 0 else 0,
        }
    
    @staticmethod
    def get_upcoming_contributions(user, days=7):
        """
        Get upcoming contribution deadlines for a user.
        
        Args:
            user: The user to check
            days: Number of days to check ahead
            
        Returns:
            QuerySet: Upcoming contributions
        """
        from mchezo.models import Contribution, Membership, Cycle
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now().date() + timedelta(days=days)
        
        return Contribution.objects.filter(
            membership__user=user,
            membership__status='active',
            cycle__status='active',
            status='pending',
            contribution_date__lte=cutoff
        ).order_by('contribution_date')
    
    @staticmethod
    def get_defaulted_members(cycle):
        """
        Get members who have not contributed in a cycle.
        
        Args:
            cycle: The cycle to check
            
        Returns:
            QuerySet: Defaulted memberships
        """
        from mchezo.models import Membership
        
        active_members = cycle.group.memberships.filter(
            status='active'
        ).exclude(
            id__in=cycle.contributions.filter(
                status='completed'
            ).values('membership_id')
        )
        
        return active_members
