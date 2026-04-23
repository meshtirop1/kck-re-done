from django.contrib import admin
from .models import Endorsement


@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'member_full_name', 'endorsement_type',
                    'status', 'issued_by', 'issued_at', 'created_at')
    list_filter = ('status', 'endorsement_type', 'created_at')
    search_fields = ('reference_number', 'member_full_name', 'member_id_number', 'subject')
    readonly_fields = ('reference_number', 'verification_code', 'created_at',
                       'updated_at', 'issued_at')
    fieldsets = (
        ('Reference', {'fields': ('reference_number', 'verification_code', 'status')}),
        ('Member', {'fields': ('user', 'member_full_name', 'member_id_number')}),
        ('Letter Content', {
            'fields': ('endorsement_type', 'subject', 'addressed_to', 'addressed_to_address',
                       'purpose', 'member_standing', 'body'),
        }),
        ('Linked Request', {'fields': ('related_service_request',), 'classes': ('collapse',)}),
        ('Validity', {'fields': ('valid_from', 'valid_until')}),
        ('Issuer', {'fields': ('issued_by', 'issued_by_name', 'issued_by_role')}),
        ('System', {'fields': ('pdf_file', 'revoke_reason', 'created_by',
                               'created_at', 'updated_at', 'issued_at')}),
    )
