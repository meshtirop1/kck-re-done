from django.db import models
from django.conf import settings


class ContactMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    replied_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class AmbassadorProfile(models.Model):
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, default='Ambassador of Kenya to Korea')
    photo = models.ImageField(upload_to='ambassador/', blank=True, null=True)
    biography = models.TextField()
    message = models.TextField(blank=True, help_text='Welcome message from the ambassador')
    email = models.EmailField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ambassador Profile'

    def __str__(self):
        return self.name


class SiteSettings(models.Model):
    """Singleton model for global site settings — everything editable via Admin Portal."""
    # Identity
    site_name = models.CharField(max_length=255, default='Kenya Community in Korea')
    site_short_name = models.CharField(max_length=50, default='KCK')
    tagline = models.CharField(max_length=500, blank=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True, help_text='Optional custom logo (otherwise uses default KCK logo)')

    # Slogan
    slogan = models.CharField(max_length=100, default='SOTE PAMOJA', help_text='Community slogan (displayed site-wide)')
    slogan_translation = models.CharField(max_length=200, default='All Together', help_text='English translation of the slogan')
    slogan_description = models.CharField(max_length=500, default='the spirit of our community', help_text='Short descriptor shown under slogan')

    # Hero (homepage)
    hero_badge_text = models.CharField(max_length=255, default='Kenyan Community · Seoul · Korea',
        help_text='Small pill text above hero title')
    hero_title = models.CharField(max_length=255, default='Kenya Community')
    hero_title_accent = models.CharField(max_length=100, default='in Korea',
        help_text='Part of hero title shown in gold')
    hero_subtitle = models.TextField(
        default='A community platform connecting, supporting and celebrating Kenyans across South Korea — events, embassy liaison, official communications, and a space that feels like home.',
        blank=True)
    hero_image = models.ImageField(upload_to='site/', blank=True, null=True)
    hero_cta_primary_text = models.CharField(max_length=100, default='Join the Community')
    hero_cta_secondary_text = models.CharField(max_length=100, default='Upcoming Events')

    # Embassy CTA section
    embassy_cta_title = models.CharField(max_length=255, default='Need Embassy Services?')
    embassy_cta_eyebrow = models.CharField(max_length=100, default='Embassy Liaison Service')
    embassy_cta_description = models.TextField(
        default='KCK helps Kenyans in Korea access embassy services through our community liaison program. Submit your request online and our officers will guide you through the process and coordinate with the Kenyan Embassy in Seoul on your behalf.')
    embassy_cta_note = models.CharField(max_length=500,
        default='Note: Official processing and document issuance is done by the Embassy of Kenya — KCK is a community facilitator, not the embassy.')

    # Membership / bank-transfer info (editable by treasurer)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_name = models.CharField(max_length=200, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    bank_swift = models.CharField(max_length=20, blank=True)
    treasurer_contact_email = models.EmailField(blank=True)
    treasurer_contact_phone = models.CharField(max_length=30, blank=True)
    membership_page_title = models.CharField(max_length=200, default='KCK Membership')
    membership_page_intro = models.TextField(
        default='Become a member of the Kenya Community in Korea. One annual fee unlocks the full benefits of belonging.')

    # Official Embassy of Kenya in Seoul
    embassy_official_url = models.URLField(
        default='https://kenya-embassy.or.kr',
        help_text='Official website of the Embassy of Kenya in Seoul')
    embassy_official_name = models.CharField(max_length=255,
        default='Embassy of the Republic of Kenya, Seoul',
        help_text='Display name of the official embassy')

    # Embassy disclaimer banner (top of every page)
    embassy_disclaimer_text = models.TextField(
        default='This is a community platform for Kenyans living in South Korea — not the official Kenya Embassy. For official embassy/consular services, please visit the Embassy of Kenya in Seoul.',
        help_text='Banner shown at top of every page')
    embassy_disclaimer_enabled = models.BooleanField(default=True, help_text='Show the embassy disclaimer banner')

    # About page
    about_text = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)

    # Footer
    footer_about = models.TextField(
        default='Supporting and connecting the Kenyan community in South Korea through embassy liaison, cultural events, and community engagement.',
        help_text='Description shown in footer')
    footer_copyright = models.CharField(max_length=255, blank=True,
        help_text='Custom copyright text (optional, defaults to "© YEAR SITE_NAME. All rights reserved.")')

    # Contact info
    email = models.EmailField(default='info@kenyakorea.com')
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    office_hours = models.CharField(max_length=255, default='Monday - Friday: 9:00 AM - 5:00 PM')

    # Social media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Newsletter
    newsletter_title = models.CharField(max_length=255, default='Subscribe to Newsletter')
    newsletter_description = models.CharField(max_length=500,
        default='Get updates on community news, events, and announcements.')

    # Discover Kenya page
    discover_hero_title = models.CharField(max_length=255, default='Discover Kenya')
    discover_hero_subtitle = models.CharField(max_length=500,
        default='The Magic of Kenya — a land of stunning landscapes, vibrant cultures, and unforgettable experiences.')
    discover_hero_image = models.ImageField(upload_to='discover/', blank=True, null=True,
        help_text='Optional hero background image for /discover/')
    discover_intro_title = models.CharField(max_length=255, default='Karibu Kenya')
    discover_intro_text = models.TextField(
        default='Kenya is a country of breathtaking beauty and remarkable diversity. From the iconic savannahs of the Maasai Mara to the snow-capped peak of Mount Kenya, from the pristine beaches of the Indian Ocean to the bustling streets of Nairobi, Kenya offers an experience like no other.\n\nHome to over 50 million people and 44 ethnic communities, Kenya is a mosaic of cultures, languages, and traditions. Swahili and English are the official languages.\n\nWhether you are seeking adventure, culture, relaxation, or business opportunities, Kenya welcomes you with open arms and unforgettable memories.')
    discover_intro_image = models.ImageField(upload_to='discover/', blank=True, null=True,
        help_text='Image shown next to the "Karibu Kenya" intro text')
    discover_culture_title = models.CharField(max_length=255, default='Culture & Heritage')
    discover_culture_text = models.TextField(
        default='Kenya\'s cultural diversity is one of its greatest treasures. The country is home to communities such as the Kikuyu, Luo, Kalenjin, Maasai, Kamba, Luhya, and many more, each with unique traditions, music, dance, and cuisine.\n\nExplore traditional crafts, attend cultural festivals, and experience the warm hospitality Kenya is known for.')
    discover_cuisine_title = models.CharField(max_length=255, default='Food & Cuisine')
    discover_cuisine_text = models.TextField(
        default='Kenyan cuisine is as diverse as its people. Savour nyama choma (grilled meat), ugali (cornmeal staple), sukuma wiki (collard greens), pilau rice, chapati, and coastal seafood dishes infused with Swahili spices.\n\nDon\'t miss a cup of Kenyan coffee or tea — globally celebrated for their rich flavour and quality.')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Site Settings'
