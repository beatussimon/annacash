"""
Audit views for ANNA platform.
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from core.models import AuditLog
from accounts.models import User
from wakala.models import Wakala, Transaction, FinancialDay
from mchezo.models import Group, Contribution, Payout

@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_reports(request):
    """System statistics and reports."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # User Stats
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Wakala Stats
    total_wakalas = Wakala.objects.count()
    total_txns = Transaction.objects.count()
    monthly_txn_volume = Transaction.objects.filter(created_at__date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0
    today_txn_volume = Transaction.objects.filter(created_at__date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Mchezo Stats
    total_groups = Group.objects.count()
    total_contributions = Contribution.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    total_payouts = Payout.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0

    return render(
        request,
        "audit/reports.html",
        {
            "page_title": "System Reports",
            "total_users": total_users,
            "active_users": active_users,
            "total_wakalas": total_wakalas,
            "total_txns": total_txns,
            "monthly_txn_volume": monthly_txn_volume,
            "today_txn_volume": today_txn_volume,
            "total_groups": total_groups,
            "total_contributions": total_contributions,
            "total_payouts": total_payouts,
        },
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_log(request):
    """View audit log."""
    logs = AuditLog.objects.select_related('user', 'content_type').order_by('-timestamp')[:100]
    
    return render(
        request,
        "audit/log.html",
        {
            "page_title": "Audit Log",
            "logs": logs,
        },
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_alerts(request):
    """View system alerts."""
    # Find any financial days with discrepancies
    discrepancy_days = FinancialDay.objects.exclude(discrepancy=0).order_by('-date')[:50]
    
    # Find any late mchezo contributions
    late_contributions = Contribution.objects.filter(is_late=True, status='completed').order_by('-contribution_date')[:50]

    return render(
        request,
        "audit/alerts.html",
        {
            "page_title": "System Alerts",
            "discrepancy_days": discrepancy_days,
            "late_contributions": late_contributions,
        },
    )
