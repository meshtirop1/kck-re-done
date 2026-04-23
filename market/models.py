"""Kenyan Market — community marketplace for approved Kenyan sellers in Korea.

Flow:
  1. Active KCK member applies to become a seller (SellerProfile, status=pending).
  2. A KCK leader reviews and approves/rejects the application.
  3. Approved sellers can create Product listings.
  4. Public browses /market/, contacts sellers via WhatsApp.
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
import re


# -----------------------------------------------------------------------------
# Categories
# -----------------------------------------------------------------------------

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=120, blank=True)
    description = models.CharField(max_length=500, blank=True)
    icon = models.CharField(max_length=10, blank=True, default='🛍️',
        help_text='Emoji or Bootstrap icon class')
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Product categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# -----------------------------------------------------------------------------
# Seller profile (application + approved seller)
# -----------------------------------------------------------------------------

SELLER_STATUS_CHOICES = [
    ('pending', 'Pending Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('suspended', 'Suspended'),
]


class SellerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='seller_profile')
    business_name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    bio = models.TextField(help_text='Tell buyers about your business and what you sell')
    profile_photo = models.ImageField(upload_to='market/sellers/', blank=True, null=True)

    # Primary contact info
    whatsapp_number = models.CharField(max_length=30,
        help_text='International format preferred: +82 10 1234 5678 or +254 7xx xxx xxx')
    phone = models.CharField(max_length=30, blank=True)
    email_contact = models.EmailField(blank=True)
    city = models.CharField(max_length=50, blank=True,
        help_text='e.g. Seoul, Busan, Incheon')
    location_notes = models.CharField(max_length=255, blank=True,
        help_text='e.g. "Near Itaewon Station" — helps buyers plan pickups')

    # Approval workflow
    status = models.CharField(max_length=20, choices=SELLER_STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='seller_applications_reviewed')
    review_notes = models.TextField(blank=True,
        help_text='Internal notes or rejection reason')

    active = models.BooleanField(default=True,
        help_text='Uncheck to temporarily hide this seller')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.business_name)
            slug = base
            i = 2
            while SellerProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.business_name} ({self.get_status_display()})'

    @property
    def is_approved(self):
        return self.status == 'approved' and self.active

    @property
    def whatsapp_link(self):
        """Build a wa.me link from the seller's WhatsApp number."""
        if not self.whatsapp_number:
            return ''
        digits = re.sub(r'\D', '', self.whatsapp_number)
        return f'https://wa.me/{digits}' if digits else ''

    @property
    def total_products(self):
        return self.products.filter(is_available=True).count()

    def get_absolute_url(self):
        return reverse('market:seller_detail', args=[self.slug])


# -----------------------------------------------------------------------------
# Products
# -----------------------------------------------------------------------------

CURRENCY_CHOICES = [
    ('KRW', '₩ KRW (Korean Won)'),
    ('USD', '$ USD'),
    ('KES', 'KSh KES (Kenyan Shilling)'),
]

DELIVERY_CHOICES = [
    ('free_korea', 'Free delivery anywhere in Korea'),
    ('free_city', 'Free delivery within my city'),
    ('paid', 'Delivery available (buyer pays)'),
    ('pickup_only', 'Pickup only — no delivery'),
    ('meetup', 'Meet-up arranged via WhatsApp'),
]

CITY_CHOICES = [
    ('seoul', 'Seoul'),
    ('busan', 'Busan'),
    ('incheon', 'Incheon'),
    ('daegu', 'Daegu'),
    ('daejeon', 'Daejeon'),
    ('gwangju', 'Gwangju'),
    ('ulsan', 'Ulsan'),
    ('other', 'Other'),
]


class Product(models.Model):
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products')

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField()

    image = models.ImageField(upload_to='market/products/',
        help_text='Main product photo')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='KRW')

    # Delivery
    free_delivery_korea = models.BooleanField(default=False,
        help_text='Free delivery anywhere in Korea')
    delivery_option = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='meetup')
    delivery_notes = models.CharField(max_length=500, blank=True,
        help_text='Details about delivery, pickup points, fees (if any)')
    city = models.CharField(max_length=20, choices=CITY_CHOICES, default='seoul',
        help_text='Where the product is located')

    # Contact override (optional — defaults to seller's WhatsApp)
    whatsapp_link_override = models.URLField(blank=True,
        help_text='Optional: custom WhatsApp link for this product (defaults to your seller WhatsApp)')
    whatsapp_message_template = models.CharField(max_length=500, blank=True,
        help_text='Pre-filled message, e.g. "Hi! I\'m interested in {product_name}"')

    is_available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        # If user ticked free_delivery_korea, normalise delivery_option
        if self.free_delivery_korea and self.delivery_option != 'free_korea':
            self.delivery_option = 'free_korea'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} — {self.seller.business_name}'

    def get_absolute_url(self):
        return reverse('market:product_detail', args=[self.slug])

    @property
    def whatsapp_chat_url(self):
        """Return the effective WhatsApp chat URL for this product."""
        if self.whatsapp_link_override:
            return self.whatsapp_link_override
        base = self.seller.whatsapp_link
        if not base:
            return ''
        msg = self.whatsapp_message_template or f"Hi! I'm interested in '{self.name}' on KCK Kenyan Market."
        from urllib.parse import quote
        return f'{base}?text={quote(msg)}'

    @property
    def price_display(self):
        if self.currency == 'KRW':
            return f'₩{int(self.price):,}'
        if self.currency == 'USD':
            return f'${self.price:,.2f}'
        if self.currency == 'KES':
            return f'KSh {int(self.price):,}'
        return f'{self.price} {self.currency}'

    @property
    def has_free_delivery(self):
        return self.free_delivery_korea or self.delivery_option in ('free_korea', 'free_city')


class ProductImage(models.Model):
    """Additional images for a product (gallery)."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='market/products/gallery/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f'Image for {self.product.name}'
