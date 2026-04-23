from django.contrib import admin
from .models import Membership, MembershipAuditLog, MembershipBenefit, MembershipPayment, MembershipTier


@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'annual_amount', 'currency', 'active', 'sort_order')
    list_editable = ('active', 'sort_order')


@admin.register(MembershipBenefit)
class MembershipBenefitAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'sort_order', 'active')
    list_editable = ('sort_order', 'active')
    search_fields = ('title',)


class MembershipPaymentInline(admin.TabularInline):
    model = MembershipPayment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('reference_code', 'user', 'member_number', 'status', 'expected_amount',
                    'period_end', 'created_at')
    list_filter = ('status', 'tier')
    search_fields = ('reference_code', 'member_number', 'user__username', 'user__email')
    readonly_fields = ('reference_code', 'created_at', 'payment_declared_at', 'activated_at')
    inlines = [MembershipPaymentInline]
    date_hierarchy = 'created_at'


@admin.register(MembershipAuditLog)
class MembershipAuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'membership', 'description_short')
    list_filter = ('action',)
    search_fields = ('description', 'actor__username', 'membership__reference_code')
    readonly_fields = [f.name for f in MembershipAuditLog._meta.fields]
    date_hierarchy = 'created_at'

    def description_short(self, obj):
        return (obj.description or '')[:80]
    description_short.short_description = 'Description'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
