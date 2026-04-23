from django.contrib import admin

from .models import VisaType, VisaApplication, PassportApplication, Faq


@admin.register(VisaType)
class VisaTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'processing_time', 'fee', 'sort_order', 'active')
    list_filter = ('active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order', 'active')
    ordering = ('sort_order', 'name')


@admin.register(VisaApplication)
class VisaApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'visa_type',
        'full_name',
        'status',
        'submitted_at',
    )
    list_filter = ('status', 'visa_type')
    search_fields = ('full_name', 'passport_number', 'user__email')
    readonly_fields = ('submitted_at',)
    list_editable = ('status',)
    list_display_links = ('user', 'full_name')
    date_hierarchy = 'submitted_at'
    actions = ('approve_applications', 'reject_applications')

    fieldsets = (
        ('Applicant', {
            'fields': ('user', 'visa_type', 'full_name', 'passport_number'),
        }),
        ('Status', {
            'fields': ('status', 'submitted_at'),
        }),
    )

    @admin.action(description='Approve selected visa applications')
    def approve_applications(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} application(s) approved.')

    @admin.action(description='Reject selected visa applications')
    def reject_applications(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} application(s) rejected.')


@admin.register(PassportApplication)
class PassportApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'type', 'status', 'submitted_at')
    list_filter = ('status', 'type')
    search_fields = ('full_name', 'national_id', 'email')
    readonly_fields = ('submitted_at',)
    list_editable = ('status',)
    date_hierarchy = 'submitted_at'
    actions = ('approve_applications', 'reject_applications')

    fieldsets = (
        ('Applicant', {
            'fields': ('full_name', 'national_id', 'email', 'type'),
        }),
        ('Status', {
            'fields': ('status', 'submitted_at'),
        }),
    )

    @admin.action(description='Approve selected passport applications')
    def approve_applications(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} application(s) approved.')

    @admin.action(description='Reject selected passport applications')
    def reject_applications(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} application(s) rejected.')


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'sort_order', 'active')
    list_filter = ('category', 'active')
    search_fields = ('question', 'answer')
    list_editable = ('sort_order', 'active')
    ordering = ('category', 'sort_order')
