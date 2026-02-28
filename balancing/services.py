"""
Balancing engine for ANNA platform.

Provides daily balancing functionality for wakala operations
with discrepancy detection and alerts.
"""

from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone


class BalancingEngine:
    """
    Engine for managing daily financial balancing.

    Key features:
    - Opening balance tracking
    - Real-time computed closing balance
    - Discrepancy detection
    - Alert generation
    """

    @staticmethod
    @db_transaction.atomic
    def open_day(user, wakala, date, opening_cash=0, opening_float=0, note=""):
        """
        Open a new financial day for a wakala.
        """
        from wakala.models import FinancialDay
        from core.services import AuditLogger

        # Check for existing open day
        open_day = wakala.get_open_financial_day()
        if open_day:
            raise ValueError(f"Financial day for {open_day.date} is still open")

        # Check if day already exists
        if FinancialDay.objects.filter(wakala=wakala, date=date).exists():
            raise ValueError(f"Financial day for {date} already exists")

        # Create and open the day
        day = FinancialDay(
            wakala=wakala,
            date=date,
            status="open",
            opening_cash=opening_cash or Decimal("0"),
            opening_float=opening_float or Decimal("0"),
            opening_balance=(opening_cash or Decimal("0")) + (opening_float or Decimal("0")),
            opening_balance_note=note,
            opened_at=timezone.now(),
            opened_by=user,
            created_by=user,
            original_recorder=user,
        )
        day.save()

        # Log the action
        AuditLogger.log_day_open_close(user=user, financial_day=day, action="open_day")

        return day

    @staticmethod
    @db_transaction.atomic
    def close_day(user, wakala, closing_cash, closing_float, note=""):
        """
        Close the current financial day.
        """
        from wakala.models import FinancialDay
        from core.services import AuditLogger

        # Get the open day
        day = wakala.get_open_financial_day()
        if not day:
            raise ValueError("No open financial day found")

        # Use the model's robust close_day logic
        day.close_day(
            user=user,
            closing_cash=closing_cash,
            closing_float=closing_float,
            note=note
        )

        # Log the action
        AuditLogger.log_day_open_close(user=user, financial_day=day, action="close_day")

        return day

    @staticmethod
    def get_day_status(wakala, date=None):
        """
        Get the balancing status for a day.
        """
        from wakala.models import FinancialDay
        from django.db.models import Sum

        if date is None:
            date = timezone.now().date()

        try:
            day = FinancialDay.objects.get(wakala=wakala, date=date)
        except FinancialDay.DoesNotExist:
            return {
                "exists": False,
                "date": date,
                "status": "not_created",
            }

        # Calculate transaction summary
        txns = day.transactions.all()
        deposits = (
            txns.filter(transaction_type="deposit").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        withdrawals = (
            txns.filter(transaction_type="withdrawal").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )

        return {
            "exists": True,
            "date": day.date,
            "status": day.status,
            "opening_balance": day.opening_balance,
            "computed_closing_balance": day.computed_closing_balance,
            "actual_closing_balance": day.closing_balance,
            "discrepancy": day.discrepancy,
            "deposits_total": deposits,
            "withdrawals_total": withdrawals,
            "transactions_count": txns.count(),
        }

    @staticmethod
    def get_discrepancy_alerts(wakala, days=7):
        """
        Get discrepancy alerts for recent days.
        """
        from wakala.models import FinancialDay
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now().date() - timedelta(days=days)

        return FinancialDay.objects.filter(
            wakala=wakala, status="closed", discrepancy__gt=0, date__gte=cutoff
        ).order_by("-date")

    @staticmethod
    def get_closing_balance_estimate(wakala, date=None):
        """
        Get estimated closing balance for a day.
        """
        from wakala.models import FinancialDay

        if date is None:
            date = timezone.now().date()

        try:
            day = FinancialDay.objects.get(wakala=wakala, date=date)
        except FinancialDay.DoesNotExist:
            return Decimal("0")

        # Result is now a dict, extract the total
        results = day.calculate_computed_balance()
        return results["total"]
