from django.contrib import admin

from .models import Event, EventRegistration, EventGalleryImage


class EventGalleryImageInline(admin.TabularInline):
    model = EventGalleryImage
    extra = 1
    fields = ('image', 'caption', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'date',
        'location',
        'capacity',
        'registration_count',
        'active',
        'featured',
    )
    list_filter = ('active', 'featured')
    search_fields = ('title', 'location')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'date'
    list_editable = ('active', 'featured')
    inlines = (EventGalleryImageInline,)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description'),
        }),
        ('Schedule & Location', {
            'fields': ('date', 'location', 'capacity'),
        }),
        ('Visibility', {
            'fields': ('active', 'featured'),
        }),
    )

    def registration_count(self, obj):
        if hasattr(obj, 'registration_count'):
            attr = obj.registration_count
            if callable(attr):
                return attr()
            return attr
        return obj.registrations.count() if hasattr(obj, 'registrations') else 0

    registration_count.short_description = 'Registrations'


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'registered_at')
    list_filter = ('status', 'event')
    search_fields = ('user__username', 'event__title')
    readonly_fields = ('registered_at',)
    list_editable = ('status',)
    date_hierarchy = 'registered_at'


@admin.register(EventGalleryImage)
class EventGalleryImageAdmin(admin.ModelAdmin):
    list_display = ('event', 'caption', 'uploaded_at')
    list_filter = ('event',)
    search_fields = ('event__title', 'caption')
    readonly_fields = ('uploaded_at',)
