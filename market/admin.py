from django.contrib import admin
from .models import SellerProfile, ProductCategory, Product, ProductImage


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'active', 'sort_order')
    list_editable = ('active', 'sort_order')
    list_filter = ('active',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'status', 'city', 'active', 'applied_at')
    list_filter = ('status', 'active', 'city')
    search_fields = ('business_name', 'user__username', 'user__email', 'whatsapp_number')
    readonly_fields = ('applied_at', 'reviewed_at', 'created_at', 'updated_at', 'slug')
    fieldsets = (
        ('Applicant', {'fields': ('user', 'business_name', 'slug', 'bio', 'profile_photo')}),
        ('Contact', {'fields': ('whatsapp_number', 'phone', 'email_contact',
                                'city', 'location_notes')}),
        ('Approval', {'fields': ('status', 'review_notes', 'reviewed_by',
                                 'applied_at', 'reviewed_at', 'active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'price', 'currency', 'city',
                    'free_delivery_korea', 'is_available', 'featured', 'created_at')
    list_filter = ('is_available', 'featured', 'category', 'city',
                   'free_delivery_korea', 'currency')
    search_fields = ('name', 'description', 'seller__business_name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    list_editable = ('is_available', 'featured')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'caption', 'order', 'uploaded_at')
