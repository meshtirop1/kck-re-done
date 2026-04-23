from django.contrib import admin
from .models import EmbassyServiceRequest, RequestNote, ServiceGuide


class RequestNoteInline(admin.TabularInline):
    model = RequestNote
    extra = 0
    readonly_fields = ('author', 'note_type', 'created_at')
    fields = ('author', 'note_type', 'message', 'is_internal', 'created_at')


@admin.register(EmbassyServiceRequest)
class EmbassyServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'full_name', 'service_type', 'status', 'priority', 'assigned_officer', 'submitted_at')
    list_filter = ('status', 'service_type', 'priority', 'submitted_at')
    search_fields = ('request_number', 'full_name', 'kenyan_id_number', 'user__email')
    readonly_fields = ('request_number', 'submitted_at', 'updated_at', 'forwarded_at', 'completed_at')
    date_hierarchy = 'submitted_at'
    inlines = [RequestNoteInline]


@admin.register(RequestNote)
class RequestNoteAdmin(admin.ModelAdmin):
    list_display = ('request', 'author', 'note_type', 'is_internal', 'created_at')
    list_filter = ('note_type', 'is_internal', 'created_at')
    search_fields = ('request__request_number', 'message')
    readonly_fields = ('created_at',)


@admin.register(ServiceGuide)
class ServiceGuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'service_type', 'typical_timeline', 'embassy_fee', 'active', 'sort_order')
    list_filter = ('active',)
    search_fields = ('title', 'description')
    list_editable = ('active', 'sort_order')
