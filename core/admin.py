from django.contrib import admin

from .models import ContactMessage, AmbassadorProfile, SiteSettings


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    date_hierarchy = 'created_at'
    list_editable = ('is_read',)
    actions = ('mark_as_read',)

    fieldsets = (
        ('Sender', {
            'fields': ('name', 'email'),
        }),
        ('Message', {
            'fields': ('subject', 'message'),
        }),
        ('Status', {
            'fields': ('is_read', 'created_at'),
        }),
    )

    @admin.action(description='Mark selected messages as read')
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')

    def has_add_permission(self, request):
        return False


@admin.register(AmbassadorProfile)
class AmbassadorProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'title')
    list_editable = ('active',)

    fieldsets = (
        ('Identity', {
            'fields': ('name', 'title', 'photo'),
        }),
        ('Biography', {
            'fields': ('biography', 'message'),
        }),
        ('Contact', {
            'fields': ('email',),
        }),
        ('Visibility', {
            'fields': ('active',),
        }),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only allow a single SiteSettings instance.
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
