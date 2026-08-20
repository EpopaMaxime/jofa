from django.contrib import admin
from django.db.models import Sum
from django.contrib.auth.models import User
from .models import RewardSetting, RewardPoint

@admin.register(RewardSetting)
class RewardSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'points_per_amount', 'amount_spent', 'bonus_points', 'bonus_threshold', 'points_to_cash_ratio', 'expiry_days')

    def has_add_permission(self, request):
        has_permission = super().has_add_permission(request)
        if has_permission and RewardSetting.objects.exists():
            return False
        return has_permission

@admin.register(RewardPoint)
class RewardPointAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'transaction_type', 'order_reference', 'created_at', 'expires_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'order_reference')
    readonly_fields = ('created_at',)

# Proxy model to show ranking in admin
class CustomerRanking(User):
    class Meta:
        proxy = True
        verbose_name = "Customer Reward Ranking"
        verbose_name_plural = "Customer Reward Rankings"

@admin.register(CustomerRanking)
class CustomerRankingAdmin(admin.ModelAdmin):
    list_display = ('get_rank', 'username', 'get_full_name', 'total_points')
    search_fields = ('username', 'first_name', 'last_name')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _total_points=Sum('reward_points__points')
        ).filter(_total_points__gt=0).order_by('-_total_points')
        return queryset

    def total_points(self, obj):
        return obj._total_points or 0
    total_points.admin_order_field = '_total_points'
    total_points.short_description = 'Total Points Earned'

    def get_rank(self, obj):
        # Calculate rank based on position in ordered queryset
        queryset = self.get_queryset(None)
        rank = list(queryset).index(obj) + 1
        if rank == 1: return "🥇 1st"
        if rank == 2: return "🥈 2nd"
        if rank == 3: return "🥉 3rd"
        return f"{rank}th"
    get_rank.short_description = 'Rank'
