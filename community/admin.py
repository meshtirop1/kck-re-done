from django.contrib import admin

from .models import Page, News, Testimonial, Announcement, DiscoverAttraction, TravelEssential


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'active', 'updated_at')
    list_filter = ('active',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('active',)
    readonly_fields = ('updated_at',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content'),
        }),
        ('Visibility', {
            'fields': ('active',),
        }),
        ('Meta', {
            'fields': ('updated_at',),
        }),
    )


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published', 'featured', 'published_at')
    list_filter = ('published', 'featured')
    search_fields = ('title', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    list_editable = ('published', 'featured')

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'excerpt', 'content'),
        }),
        ('Publishing', {
            'fields': ('published', 'featured', 'published_at'),
        }),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'active', 'created_at')
    list_filter = ('active',)
    search_fields = ('name', 'message')
    list_editable = ('active',)
    readonly_fields = ('created_at',)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'active', 'starts_at', 'ends_at')
    list_filter = ('level', 'active')
    search_fields = ('title', 'message')
    list_editable = ('active',)

    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'level'),
        }),
        ('Schedule', {
            'fields': ('active', 'starts_at', 'ends_at'),
        }),
    )


@admin.register(DiscoverAttraction)
class DiscoverAttractionAdmin(admin.ModelAdmin):
    list_display = ('title', 'sort_order', 'featured', 'active', 'created_at')
    list_filter = ('active', 'featured')
    list_editable = ('sort_order', 'featured', 'active')
    search_fields = ('title', 'short_description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(TravelEssential)
class TravelEssentialAdmin(admin.ModelAdmin):
    list_display = ('title', 'value', 'icon', 'sort_order', 'active')
    list_editable = ('value', 'sort_order', 'active')
    list_filter = ('active',)
    search_fields = ('title', 'value')
