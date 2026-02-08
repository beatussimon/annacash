"""
Dashboard views for ANNA platform.

Provides real data loading for all dashboards:
- Wakala dashboard with real transactions, balances
- Mchezo dashboard with real contributions, payouts
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


class DashboardMixin:
    """Mixin for common dashboard functionality."""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        from core.models import WakalaRole, MchezoRole
        
        wakala_roles = WakalaRole.objects.filter(
            user=user,
            is_active=True
        ).select_related('wakala')
        
        wakalas = [role.wakala for role in wakala_roles]
        
        mchezo_roles = MchezoRole.objects.filter(
            user=user,
            is_active=True
        ).select_related('group')
        
        groups = [role.group for role in mchezo_roles]
        
        context.update({
            'wakalas': wakalas,
            'wakala_roles': wakala_roles,
            'mchezo_groups': groups,
            'mchezo_roles': mchezo_roles,
            'has_wakala_access': len(wakalas) > 0,
            'has_mchezo_access': len(groups) > 0,
        })
        
        return context


class HomepageView(DashboardMixin, TemplateView):
    """Homepage view - redirects to appropriate dashboard based on user access."""
    template_name = 'dashboard/home.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if request.user.is_superuser:
            return redirect('dashboard:admin')
        
        ctx = self.get_context_data()
        wakalas = ctx['wakalas']
        groups = ctx['mchezo_groups']
        
        if len(wakalas) == 1 and len(groups) == 0:
            return redirect('dashboard:wakala', wakala_id=wakalas[0].id)
        elif len(wakalas) == 0 and len(groups) == 1:
            return redirect('dashboard:mchezo', group_id=groups[0].id)
        elif len(wakalas) > 0 or len(groups) > 0:
            return super().get(request, *args, **kwargs)
        else:
            return render(request, 'dashboard/no_access.html')


class AppSwitcherView(DashboardMixin, TemplateView):
    """App switcher view - main entry point after login."""
    template_name = 'dashboard/app_switcher.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return redirect('dashboard:admin')
        
        ctx = self.get_context_data()
        wakalas = ctx['wakalas']
        groups = ctx['mchezo_groups']
        
        if len(wakalas) == 1 and len(groups) == 0:
            return redirect('wakala:dashboard', wakala_id=wakalas[0].id)
        elif len(wakalas) == 0 and len(groups) == 1:
            return redirect('mchezo:dashboard', group_id=groups[0].id)
        elif len(wakalas) > 0 or len(groups) > 0:
            return super().get(request, *args, **kwargs)
        else:
            return render(request, 'dashboard/no_access.html')


class AdminDashboardView(DashboardMixin, TemplateView):
    """Superadmin dashboard."""
    template_name = 'dashboard/admin.html'
    
    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from accounts.models import User
        from wakala.models import Wakala
        from mchezo.models import Group
        from core.models import AuditLog
        
        context = super().get_context_data(**kwargs)
        
        # Get date range for recent activity
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        context.update({
            'page_title': 'Admin Dashboard - ANNA',
            'total_users': User.objects.filter(is_active=True).count(),
            'total_wakalas': Wakala.objects.filter(is_active=True).count(),
            'total_groups': Group.objects.filter(is_active=True).count(),
            'recent_audit_logs': AuditLog.objects.all()[:20],
            'today': today,
        })
        
        return context


class WakalaDashboardView(DashboardMixin, TemplateView):
    """Wakala-specific dashboard with real data."""
    template_name = 'dashboard/wakala.html'
    
    def get(self, request, wakala_id, *args, **kwargs):
        from wakala.models import Wakala
        from core.permissions import has_wakala_role
        from django.db.models import Sum
        
        try:
            wakala = Wakala.objects.get(pk=wakala_id)
        except Wakala.DoesNotExist:
            return render(request, '404.html', status=404)
        
        if not has_wakala_role(request.user, wakala, ['owner', 'manager', 'agent']):
            return render(request, 'dashboard/no_access.html', status=403)
        
        return super().get(request, wakala_id=wakala_id, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        from wakala.models import Transaction
        from core.models import WakalaRole
        
        context = super().get_context_data(**kwargs)
        wakala_id = self.kwargs['wakala_id']
        
        from wakala.models import Wakala
        wakala = Wakala.objects.get(pk=wakala_id)
        open_day = wakala.get_open_financial_day()
        
        # Get today's transactions if day is open
        today = timezone.now().date()
        today_transactions = Transaction.objects.filter(
            wakala=wakala,
            created_at__date=today,
            is_deleted=False
        ).select_related('created_by', 'network', 'bank')
        
        # Calculate real totals
        deposits_total = today_transactions.filter(
            transaction_type='deposit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        withdrawals_total = today_transactions.filter(
            transaction_type='withdrawal'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        transactions_count = today_transactions.count()
        
        # Get recent transactions for display
        recent_transactions = today_transactions.order_by('-created_at')[:10]
        
        context.update({
            'page_title': f'{wakala.name} Dashboard',
            'wakala': wakala,
            'open_day': open_day,
            # Real data - no placeholders!
            'transactions': recent_transactions,
            'today_deposits': deposits_total,
            'today_withdrawals': withdrawals_total,
            'today_transactions_count': transactions_count,
            'today': today,
        })
        
        return context


class MchezoDashboardView(DashboardMixin, TemplateView):
    """Mchezo group-specific dashboard with real data."""
    template_name = 'dashboard/mchezo.html'
    
    def get(self, request, group_id, *args, **kwargs):
        from mchezo.models import Group
        from core.permissions import has_mchezo_role
        
        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            return render(request, '404.html', status=404)
        
        if not has_mchezo_role(request.user, group, ['admin', 'treasurer', 'member']):
            return render(request, 'dashboard/no_access.html', status=403)
        
        return super().get(request, group_id=group_id, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        from mchezo.models import Group, Contribution, Payout, Membership
        from django.db.models import Sum
        from mchezo.services import MchezoService
        
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs['group_id']
        
        group = Group.objects.get(pk=group_id)
        current_cycle = group.get_current_cycle()
        
        # Get memberships
        memberships = Membership.objects.filter(
            group=group,
            is_deleted=False,
            status='active'
        ).select_related('user').order_by('payout_order')
        
        # Calculate real totals
        if current_cycle:
            contributions_total = Contribution.objects.filter(
                cycle=current_cycle,
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            payouts_total = Payout.objects.filter(
                cycle=current_cycle,
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            contributions_count = Contribution.objects.filter(
                cycle=current_cycle,
                status='completed'
            ).count()
            
            # Get cycle progress
            progress = MchezoService.get_cycle_progress(current_cycle)
            
            # Get next payout member
            next_payout_order = current_cycle.payouts_made + 1
            next_payout_member = memberships.filter(
                payout_order=next_payout_order
            ).first()
        else:
            contributions_total = 0
            payouts_total = 0
            contributions_count = 0
            progress = None
            next_payout_member = None
        
        context.update({
            'page_title': f'{group.name} Dashboard',
            'group': group,
            'current_cycle': current_cycle,
            # Real data - no placeholders!
            'memberships': memberships,
            'contributions_total': contributions_total,
            'payouts_total': payouts_total,
            'contributions_count': contributions_count,
            'progress': progress,
            'next_payout_member': next_payout_member,
            'total_expected': group.contribution_amount * group.get_member_count(),
            'remaining': (group.contribution_amount * group.get_member_count()) - contributions_total,
        })
        
        return context


class SettingsView(DashboardMixin, TemplateView):
    """User settings page."""
    template_name = 'dashboard/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current theme from localStorage (passed via JavaScript)
        context.update({
            'page_title': 'Settings - ANNA',
        })
        
        return context
