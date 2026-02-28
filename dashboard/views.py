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
            user=user, is_active=True
        ).select_related("wakala")

        wakalas = [role.wakala for role in wakala_roles]

        mchezo_roles = MchezoRole.objects.filter(
            user=user, is_active=True
        ).select_related("group")

        groups = [role.group for role in mchezo_roles]

        context.update(
            {
                "wakalas": wakalas,
                "wakala_roles": wakala_roles,
                "mchezo_groups": groups,
                "mchezo_roles": mchezo_roles,
                "has_wakala_access": len(wakalas) > 0,
                "has_mchezo_access": len(groups) > 0,
            }
        )

        return context


class HomepageView(DashboardMixin, TemplateView):
    """Homepage view - redirects to appropriate dashboard based on user access."""

    template_name = "dashboard/home.html"

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        if request.user.is_superuser:
            return redirect("dashboard:admin")

        ctx = self.get_context_data()
        wakalas = ctx["wakalas"]
        groups = ctx["mchezo_groups"]

        if len(wakalas) == 1 and len(groups) == 0:
            return redirect("dashboard:wakala", wakala_id=wakalas[0].id)
        elif len(wakalas) == 0 and len(groups) == 1:
            return redirect("dashboard:mchezo", group_id=groups[0].id)
        elif len(wakalas) > 0 or len(groups) > 0:
            return super().get(request, *args, **kwargs)
        else:
            return render(request, "dashboard/no_access.html")


class AppSwitcherView(DashboardMixin, TemplateView):
    """App switcher view - main entry point after login."""

    template_name = "dashboard/app_switcher.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return redirect("dashboard:admin")

        ctx = self.get_context_data()
        wakalas = ctx["wakalas"]
        groups = ctx["mchezo_groups"]

        if len(wakalas) == 1 and len(groups) == 0:
            return redirect("wakala:dashboard", wakala_id=wakalas[0].id)
        elif len(wakalas) == 0 and len(groups) == 1:
            return redirect("mchezo:dashboard", group_id=groups[0].id)
        elif len(wakalas) > 0 or len(groups) > 0:
            return super().get(request, *args, **kwargs)
        else:
            return render(request, "dashboard/no_access.html")


class AdminDashboardView(DashboardMixin, TemplateView):
    """Superadmin dashboard."""

    template_name = "dashboard/admin.html"

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

        context.update(
            {
                "page_title": "Admin Dashboard - ANNA",
                "total_users": User.objects.filter(is_active=True).count(),
                "total_wakalas": Wakala.objects.filter(is_active=True).count(),
                "total_groups": Group.objects.filter(is_active=True).count(),
                "recent_audit_logs": AuditLog.objects.all()[:20],
                "today": today,
            }
        )

        return context


class WakalaDashboardView(DashboardMixin, TemplateView):
    """Wakala-specific dashboard with real data and heavy analytics."""

    template_name = "dashboard/wakala.html"

    def get(self, request, wakala_id, *args, **kwargs):
        from wakala.models import Wakala
        from core.permissions import has_wakala_role

        try:
            wakala = Wakala.objects.get(pk=wakala_id)
        except Wakala.DoesNotExist:
            return render(request, "404.html", status=404)

        if not has_wakala_role(request.user, wakala, ["owner", "manager", "agent"]):
            return render(request, "dashboard/no_access.html", status=403)

        return super().get(request, wakala_id=wakala_id, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from django.db.models import Sum, Count, Avg
        from django.db.models.functions import ExtractHour
        from wakala.models import Transaction, FinancialDay
        from core.models import WakalaRole
        import json

        context = super().get_context_data(**kwargs)
        wakala_id = self.kwargs["wakala_id"]

        from wakala.models import Wakala

        wakala = Wakala.objects.get(pk=wakala_id)
        open_day = wakala.get_open_financial_day()

        # Date range for analytics (last 30 days)
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)

        # Base QuerySet for performance
        base_txns = Transaction.objects.filter(wakala=wakala, is_deleted=False)

        # 1. Operational Day Totals (Wakala context: transactions in the open day)
        # We filter by financial_day instead of just today's date
        if open_day:
            operational_transactions = base_txns.filter(financial_day=open_day).select_related(
                "created_by", "network"
            )
        else:
            operational_transactions = base_txns.filter(created_at__date=today).select_related(
                "created_by", "network"
            )

        deposits_total = (
            operational_transactions.filter(transaction_type="deposit").aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )
        withdrawals_total = (
            operational_transactions.filter(transaction_type="withdrawal").aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0
        )

        # 2. Hourly Activity (Analytics Heavy)
        hourly_data = (
            base_txns.filter(created_at__date__gte=month_ago)
            .annotate(hour=ExtractHour("created_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        # 3. Customer Insights
        top_customers = (
            base_txns.values("customer_phone", "customer_name")
            .annotate(total_spent=Sum("amount"), count=Count("id"))
            .order_by("-total_spent")[:5]
        )

        # 4. Network Popularity
        network_share = (
            base_txns.values("network__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # 5. Commission Estimate (Simulated based on common TZ rates: 0.1% for deposits, 0.5% for withdrawals)
        est_commission = (float(deposits_total) * 0.001) + (
            float(withdrawals_total) * 0.005
        )

        context.update(
            {
                "page_title": f"{wakala.name} Analytics Dashboard",
                "wakala": wakala,
                "open_day": open_day,
                "transactions": operational_transactions.order_by("-transaction_timestamp")[:10],
                "today_deposits": deposits_total,
                "today_withdrawals": withdrawals_total,
                "today_transactions_count": operational_transactions.count(),
                "est_commission": est_commission,
                "top_customers": top_customers,
                "network_share": network_share,
                "hourly_data_json": json.dumps(list(hourly_data)),
                "today": today,
            }
        )

        return context


class MchezoDashboardView(DashboardMixin, TemplateView):
    """Mchezo group-specific dashboard with real data and heavy analytics."""

    template_name = "dashboard/mchezo.html"

    def get(self, request, group_id, *args, **kwargs):
        from mchezo.models import Group
        from core.permissions import has_mchezo_role

        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            return render(request, "404.html", status=404)

        if not has_mchezo_role(request.user, group, ["admin", "treasurer", "member"]):
            return render(request, "dashboard/no_access.html", status=403)

        return super().get(request, group_id=group_id, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from mchezo.models import Group, Contribution, Payout, Membership
        from django.db.models import Sum, Count, Q
        from mchezo.services import MchezoService

        context = super().get_context_data(**kwargs)
        group_id = self.kwargs["group_id"]

        group = Group.objects.get(pk=group_id)
        current_cycle = group.get_current_cycle()

        memberships = (
            Membership.objects.filter(group=group, is_deleted=False, status="active")
            .select_related("user")
            .order_by("payout_order")
        )

        # 1. Group Health Analytics
        if current_cycle:
            total_expected_to_date = (
                group.contribution_amount
                * memberships.count()
                * current_cycle.get_current_week()
            )
            contributions_total = (
                current_cycle.contributions.filter(status="completed").aggregate(
                    Sum("amount")
                )["amount__sum"]
                or 0
            )

            # Health Score (Collection Rate)
            health_score = (
                (float(contributions_total) / float(total_expected_to_date) * 100)
                if total_expected_to_date > 0
                else 100
            )

            # Late vs On-time
            late_count = current_cycle.contributions.filter(is_late=True).count()
            ontime_count = current_cycle.contributions.filter(is_late=False).count()

            # Social Fund balance
            social_fund_balance = (
                current_cycle.contributions.aggregate(Sum("social_fund_amount"))[
                    "social_fund_amount__sum"
                ]
                or 0
            )

            progress = MchezoService.get_cycle_progress(current_cycle)
            next_payout_member = memberships.filter(
                payout_order=current_cycle.payouts_made + 1
            ).first()
            week_range = range(1, memberships.count() + 1)
        else:
            contributions_total = 0
            health_score = 0
            late_count = 0
            ontime_count = 0
            social_fund_balance = 0
            progress = None
            next_payout_member = None
            week_range = []

        # 2. Reliability Ranking
        reliability_rank = sorted(
            memberships, key=lambda m: m.trust_score, reverse=True
        )

        context.update(
            {
                "page_title": f"{group.name} Health Dashboard",
                "group": group,
                "current_cycle": current_cycle,
                "memberships": memberships,
                "reliability_rank": reliability_rank,
                "health_score": round(health_score, 1),
                "late_count": late_count,
                "ontime_count": ontime_count,
                "social_fund_balance": social_fund_balance,
                "contributions_total": contributions_total,
                "progress": progress,
                "next_payout_member": next_payout_member,
                "total_expected": group.contribution_amount * memberships.count(),
                "remaining": (group.contribution_amount * memberships.count())
                - contributions_total,
                "week_range": week_range,
            }
        )

        return context


class SettingsView(DashboardMixin, TemplateView):
    """User settings page."""

    template_name = "dashboard/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get current theme from localStorage (passed via JavaScript)
        context.update(
            {
                "page_title": "Settings - ANNA",
            }
        )

        return context
