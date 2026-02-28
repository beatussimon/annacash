from django.contrib import admin
from .models import Network, Bank, FeeRule, CommissionRule, Currency


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "hotline")
    search_fields = ("name", "code")


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "swift_code")
    search_fields = ("name", "code", "swift_code")


@admin.register(FeeRule)
class FeeRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "transaction_type",
        "fee_type",
        "is_active",
        "priority",
    )
    list_filter = ("is_active", "transaction_type", "fee_type", "network", "bank")
    search_fields = ("name", "description")
    autocomplete_fields = ["network", "bank"]


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "transaction_type",
        "commission_type",
        "is_active",
        "priority",
    )
    list_filter = ("is_active", "transaction_type", "commission_type", "network")
    search_fields = ("name", "description")
    autocomplete_fields = ["network"]


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "symbol", "is_active", "is_default")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "code")
