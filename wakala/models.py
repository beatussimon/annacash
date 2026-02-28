"""
Wakala domain models for ANNA financial platform.

This module contains all models for managing wakala (agent-based money operations)
including businesses, financial days, transactions, and balancing.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

from core.models import AuditableModel


class Wakala(AuditableModel):
    """
    A wakala business entity.

    Represents a physical or virtual business that performs
    financial operations (deposits, withdrawals, transfers).
    """

    name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    tin = models.CharField(max_length=20, blank=True, null=True)

    phone_number = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    region = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="wakala_owned"
    )

    is_active = models.BooleanField(default=True)
    allows_agents = models.BooleanField(default=True)
    requires_manager_approval = models.BooleanField(default=False)
    established_date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = "Wakala"
        verbose_name_plural = "Wakalas"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_open_financial_day(self):
        return self.financial_days.filter(status="open").first()

    def get_latest_financial_day(self):
        return self.financial_days.order_by("-date").first()

    def can_open_new_day(self):
        return self.get_open_financial_day() is None


class FinancialDay(AuditableModel):
    """
    Represents a single business day for a wakala.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("open", "Open"),
        ("closing", "Closing"),
        ("closed", "Closed"),
    ]

    wakala = models.ForeignKey(
        Wakala, on_delete=models.CASCADE, related_name="financial_days"
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Cash vs Float tracking
    opening_cash = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    opening_float = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    opening_balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    opening_balance_note = models.TextField(blank=True)

    computed_closing_cash = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    computed_closing_float = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    computed_closing_balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    closing_cash = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    closing_float = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    closing_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    closing_balance_note = models.TextField(blank=True)

    discrepancy = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discrepancy_note = models.TextField(blank=True)

    opened_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_days_opened",
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_days_closed",
    )

    class Meta:
        unique_together = ("wakala", "date")
        ordering = ["-date"]
        verbose_name = "Financial Day"
        verbose_name_plural = "Financial Days"

    def __str__(self):
        return f"{self.wakala.name} - {self.date} ({self.get_status_display()})"

    def open_day(self, user, opening_cash=0, opening_float=0, note=""):
        if self.status != "draft":
            raise ValueError("Only draft days can be opened")

        from decimal import Decimal

        self.status = "open"
        self.opening_cash = opening_cash or Decimal("0")
        self.opening_float = opening_float or Decimal("0")
        self.opening_balance = self.opening_cash + self.opening_float
        self.opening_balance_note = note
        self.opened_at = timezone.now()
        self.opened_by = user
        self.save()
        return self

    def close_day(self, user, closing_cash, closing_float, note=""):
        if self.status != "open":
            raise ValueError("Only open days can be closed")

        from decimal import Decimal

        results = self.calculate_computed_balance()
        self.computed_closing_cash = results["cash"]
        self.computed_closing_float = results["float"]
        self.computed_closing_balance = results["total"]

        self.closing_cash = closing_cash or Decimal("0")
        self.closing_float = closing_float or Decimal("0")
        self.closing_balance = self.closing_cash + self.closing_float

        self.discrepancy = self.computed_closing_balance - self.closing_balance
        self.closing_balance_note = note
        self.status = "closed"
        self.closed_at = timezone.now()
        self.closed_by = user
        self.save()
        return self

    def calculate_computed_balance(self):
        """
        Calculates computed cash and float balances based on transactions.
        Deposit: Cash increases (+), Float decreases (-)
        Withdrawal: Cash decreases (-), Float increases (+)
        """
        from django.db.models import Sum
        from decimal import Decimal

        # Handle None values for existing records
        op_cash = self.opening_cash or Decimal("0")
        op_float = self.opening_float or Decimal("0")

        # Cash movements
        cash_in = (
            self.transactions.filter(transaction_type="deposit").aggregate(
                Sum("amount")
            )["amount__sum"]
            or Decimal("0")
        )

        cash_out = (
            self.transactions.filter(transaction_type="withdrawal").aggregate(
                Sum("amount")
            )["amount__sum"]
            or Decimal("0")
        )

        # Float movements
        float_out = cash_in  # In a deposit, float goes out
        float_in = cash_out  # In a withdrawal, float comes in

        computed_cash = op_cash + cash_in - cash_out
        computed_float = op_float + float_in - float_out

        return {
            "cash": computed_cash,
            "float": computed_float,
            "total": computed_cash + computed_float,
        }

    def is_editable(self):
        return self.status in ("draft", "open")

    def is_balanced(self):
        if self.status != "closed":
            return True
        return self.discrepancy == 0


class Transaction(AuditableModel):
    """
    Core financial transaction model.

    Every transaction MUST be:
    - Entered manually by a logged-in user
    - Saved instantly (no drafts, no batching)
    - Timestamped precisely
    - Attributed to the exact user who recorded it
    """

    TRANSACTION_TYPES = [
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("transfer_in", "Transfer In"),
        ("transfer_out", "Transfer Out"),
        ("fee", "Fee"),
        ("commission", "Commission"),
        ("adjustment", "Adjustment"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    wakala = models.ForeignKey(
        Wakala, on_delete=models.PROTECT, related_name="transactions"
    )
    financial_day = models.ForeignKey(
        FinancialDay, on_delete=models.PROTECT, related_name="transactions"
    )

    transaction_code = models.CharField(max_length=50, unique=True)

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField(max_length=3, default="TZS")

    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_reference = models.CharField(max_length=100, blank=True)

    payment_method = models.CharField(max_length=50)
    network = models.ForeignKey(
        "config.Network",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    bank = models.ForeignKey(
        "config.Bank",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    reference_number = models.CharField(max_length=100, blank=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="completed"
    )
    transaction_timestamp = models.DateTimeField(default=timezone.now)

    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-transaction_timestamp", "-created_at"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.transaction_code}: {self.get_transaction_type_display()} {self.amount}"

    def save(self, *args, **kwargs):
        if not self.transaction_code:
            self.transaction_code = self._generate_transaction_code()

        # Smart Network Detection for Tanzania (Turbo-Entry)
        if self.customer_phone and not self.network:
            from config.models import Network

            # Clean number to get prefix
            clean_phone = self.customer_phone.replace("+", "").replace(" ", "")
            if clean_phone.startswith("255"):
                clean_phone = "0" + clean_phone[3:]

            prefix = clean_phone[:3]
            network_map = {
                "074": "VODA",
                "075": "VODA",
                "076": "VODA",
                "065": "TIGO",
                "067": "TIGO",
                "071": "TIGO",
                "068": "AIRTEL",
                "069": "AIRTEL",
                "078": "AIRTEL",
                "061": "HALO",
                "062": "HALO",
                "077": "ZANTEL",
            }

            network_code = network_map.get(prefix)
            if network_code:
                try:
                    self.network = Network.objects.get(code=network_code)
                except Network.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def _generate_transaction_code(self):
        import uuid

        date_str = timezone.now().strftime("%Y%m%d")
        short_uuid = str(uuid.uuid4())[:8].upper()
        return f"TXN{date_str}-{short_uuid}"

    def is_editable(self):
        return self.financial_day.status in ("draft", "open")

    def is_deletable(self):
        return self.financial_day.status == "open"
