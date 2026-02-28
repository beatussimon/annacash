from django.contrib import admin
from .models import Wakala, FinancialDay, Transaction


class TransactionInline(admin.TabularInline):
    """
    Inline for showing transactions within a Financial Day.
    Read-only for historical purposes.
    """

    model = Transaction
    extra = 0
    fields = (
        "transaction_code",
        "transaction_type",
        "amount",
        "network",
        "status",
        "created_by",
        "created_at",
    )
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Wakala)
class WakalaAdmin(admin.ModelAdmin):
    """
    Admin for Wakala business entities.
    """

    list_display = ("name", "owner", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "owner__email")
    autocomplete_fields = ["owner"]
    ordering = ("-created_at",)


@admin.register(FinancialDay)
class FinancialDayAdmin(admin.ModelAdmin):
    """
    Admin for managing financial days.
    """

    list_display = (
        "date",
        "wakala",
        "status",
        "opening_balance",
        "computed_closing_balance",
        "closing_balance",
        "discrepancy",
    )
    list_filter = ("status", "date", "wakala__name")
    search_fields = ("wakala__name", "date")
    readonly_fields = (
        "computed_closing_balance",
        "computed_closing_cash",
        "computed_closing_float",
        "discrepancy",
        "opened_at",
        "opened_by",
        "closed_at",
        "closed_by",
    )
    autocomplete_fields = ["wakala", "opened_by", "closed_by"]
    ordering = ("-date",)

    fieldsets = (
        (
            "Overview",
            {
                "fields": ("wakala", "date", "status"),
            },
        ),
        (
            "Opening Figures",
            {
                "fields": (
                    "opening_cash",
                    "opening_float",
                    "opening_balance",
                    "opening_balance_note",
                )
            },
        ),
        (
            "Closing Figures",
            {
                "fields": (
                    "closing_cash",
                    "closing_float",
                    "closing_balance",
                    "closing_balance_note",
                )
            },
        ),
        (
            "System Computed",
            {
                "classes": ("collapse",),
                "fields": (
                    "computed_closing_cash",
                    "computed_closing_float",
                    "computed_closing_balance",
                    "discrepancy",
                ),
            },
        ),
        (
            "Audit Trail",
            {
                "classes": ("collapse",),
                "fields": ("opened_at", "opened_by", "closed_at", "closed_by"),
            },
        ),
    )

    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin for all wakala transactions.
    """

    list_display = (
        "transaction_code",
        "financial_day",
        "transaction_type",
        "amount",
        "network",
        "status",
        "created_at",
    )
    list_filter = ("transaction_type", "status", "network", "financial_day__date")
    search_fields = (
        "transaction_code",
        "customer_phone",
        "customer_name",
        "reference_number",
    )
    readonly_fields = ("transaction_code", "created_at", "updated_at", "created_by")
    autocomplete_fields = ["financial_day", "network", "bank", "created_by"]
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Core Details",
            {
                "fields": (
                    "financial_day",
                    "transaction_code",
                    "transaction_type",
                    "amount",
                    "status",
                )
            },
        ),
        (
            "Customer & Payment",
            {
                "fields": (
                    "customer_name",
                    "customer_phone",
                    "payment_method",
                    "network",
                    "bank",
                    "reference_number",
                )
            },
        ),
        ("Notes & Audit", {"fields": ("notes", "created_at", "created_by")}),
    )
