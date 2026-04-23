from django.contrib import admin

from .models import Communication, Announcement, CommunicationDelivery


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'subject', 'category', 'audience', 'status', 'published_at', 'created_at')
    list_filter = ('status', 'category', 'audience', 'published_at')
    search_fields = ('reference_number', 'subject', 'body')
    readonly_fields = ('reference_number', 'created_at', 'updated_at', 'published_at')
    date_hierarchy = 'created_at'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'is_pinned', 'published_at', 'created_at')
    list_filter = ('category', 'is_published', 'is_pinned')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'published_at')


@admin.register(CommunicationDelivery)
class CommunicationDeliveryAdmin(admin.ModelAdmin):
    list_display = ('communication', 'user', 'delivered_at', 'read_at')
    list_filter = ('delivered_at', 'read_at')
    search_fields = ('communication__reference_number', 'user__username', 'user__email')
