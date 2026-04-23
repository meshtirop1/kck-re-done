from django.contrib import admin
from django.contrib import messages
from .models import Certificate
from .services import issue_certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('cert_number', 'recipient_name', 'cert_type', 'status', 'issued_date', 'issued_by')
    list_filter = ('status', 'cert_type')
    search_fields = ('cert_number', 'recipient_name')
    readonly_fields = ('cert_number', 'verification_code', 'created_at', 'updated_at')
    actions = ['publish_selected']

    fieldsets = (
        ('Identifiers', {
            'fields': ('cert_number', 'verification_code', 'status'),
        }),
        ('Recipient', {
            'fields': ('recipient_user', 'recipient_name'),
        }),
        ('Certificate Content', {
            'fields': ('cert_type', 'title', 'body', 'event_title', 'issued_date'),
        }),
        ('Issuer', {
            'fields': ('issued_by', 'issued_by_name', 'issued_by_role'),
        }),
        ('Output', {
            'fields': ('pdf_file',),
        }),
        ('Revocation', {
            'fields': ('revoke_reason',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def publish_selected(self, request, queryset):
        success = 0
        failed = 0
        for cert in queryset:
            try:
                issue_certificate(cert, request=request)
                success += 1
            except Exception as e:
                failed += 1
                self.message_user(request, f'Failed to publish {cert.cert_number}: {e}', level=messages.ERROR)
        if success:
            self.message_user(request, f'{success} certificate(s) published successfully.', level=messages.SUCCESS)
        if failed:
            self.message_user(request, f'{failed} certificate(s) failed to publish.', level=messages.WARNING)

    publish_selected.short_description = 'Publish selected certificates (generate PDFs)'
