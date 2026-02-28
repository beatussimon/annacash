from django.contrib import admin
from .models import Group, Membership, Cycle, Contribution, Payout


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1
    autocomplete_fields = ["user"]
    verbose_name = "Member"
    verbose_name_plural = "Members"


class ContributionInline(admin.TabularInline):
    model = Contribution
    extra = 0
    fields = ("membership", "amount", "contribution_week", "is_late", "status")
    readonly_fields = fields
    can_delete = False
    autocomplete_fields = ["membership"]

    def has_add_permission(self, request, obj=None):
        return False


class PayoutInline(admin.TabularInline):
    model = Payout
    extra = 0
    fields = ("membership", "amount", "net_amount", "status", "scheduled_date")
    readonly_fields = fields
    can_delete = False
    autocomplete_fields = ["membership"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "contribution_amount",
        "contribution_frequency",
        "max_members",
        "payout_order_method",
        "is_active",
    )
    list_filter = ("is_active", "contribution_frequency", "payout_order_method")
    search_fields = ("name", "description")
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "group", "status", "join_date", "trust_score")
    list_filter = ("status", "group__name")
    search_fields = ("user__email", "user__first_name", "group__name")
    autocomplete_fields = ["user", "group"]
    readonly_fields = ("trust_score",)


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "start_date",
        "end_date",
        "status",
        "get_total_contributions",
        "payouts_made",
    )
    list_filter = ("status", "group__name")
    search_fields = ("group__name",)
    autocomplete_fields = ["group"]
    readonly_fields = (
        "get_total_contributions",
        "total_payouts",
        "payouts_made",
        "get_social_fund_balance",
        "get_fines_collected",
    )
    inlines = [ContributionInline, PayoutInline]

    def get_queryset(self, request):
        # Prefetch related data to optimize performance
        return (
            super()
            .get_queryset(request)
            .prefetch_related("contributions")
            .annotate(
                total_contrib=models.Sum("contributions__amount"),
                social_fund=models.Sum("contributions__social_fund_amount"),
                fines=models.Sum("contributions__fine_amount"),
            )
        )

    @admin.display(description="Total Contributions")
    def get_total_contributions(self, obj):
        return obj.total_contrib or 0

    @admin.display(description="Social Fund")
    def get_social_fund_balance(self, obj):
        return obj.social_fund or 0

    @admin.display(description="Fines Collected")
    def get_fines_collected(self, obj):
        return obj.fines or 0



@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = (
        "membership",
        "cycle",
        "amount",
        "contribution_week",
        "is_late",
        "status",
        "contribution_date",
    )
    list_filter = ("status", "is_late", "cycle__group__name", "contribution_date")
    search_fields = ("membership__user__email", "cycle__group__name")
    autocomplete_fields = ["cycle", "membership"]
    ordering = ("-contribution_date",)


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = (
        "membership",
        "cycle",
        "amount",
        "bid_amount",
        "net_amount",
        "status",
        "scheduled_date",
    )
    list_filter = ("status", "cycle__group__name")
    search_fields = ("membership__user__email", "cycle__group__name")
    autocomplete_fields = ["cycle", "membership"]
    ordering = ("-scheduled_date",)
