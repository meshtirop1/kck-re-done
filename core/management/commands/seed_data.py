from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from services.models import VisaType, Faq
from events_app.models import Event
from community.models import News, Testimonial, Announcement, Page, DiscoverAttraction, TravelEssential
from core.models import AmbassadorProfile, SiteSettings, ContactMessage
from accounts.models import NewsletterSubscription
from leaders.models import Leader
from certificates.models import Certificate
from communications.models import Communication, Announcement as CommAnnouncement
from embassy_liaison.models import ServiceGuide
from sports.models import Sport, Team, Player, Competition, Fixture, SportsEvent, SportsNews
from market.models import ProductCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample data for KCK website'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Clear data before seeding')

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('Clearing data...'))
            VisaType.objects.all().delete()
            Faq.objects.all().delete()
            Event.objects.all().delete()
            News.objects.all().delete()
            Testimonial.objects.all().delete()
            Announcement.objects.all().delete()
            Page.objects.all().delete()
            ContactMessage.objects.all().delete()
            Leader.objects.all().delete()
            Certificate.objects.all().delete()
            Communication.objects.all().delete()
            CommAnnouncement.objects.all().delete()
            ServiceGuide.objects.all().delete()

        self.stdout.write('Seeding data...')
        self.create_users()
        self.create_leaders()
        self.create_site_settings()
        self.create_ambassador()
        self.create_visa_types()
        self.create_faqs()
        self.create_events()
        self.create_news()
        self.create_testimonials()
        self.create_announcements()
        self.create_pages()
        self.create_contact_messages()
        self.create_certificates()
        self.create_communications()
        self.create_comm_announcements()
        self.create_service_guides()
        self.create_sports_data()
        self.create_market_categories()
        self.create_discover_content()
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
        self.stdout.write(self.style.SUCCESS('Admin: admin@kenyakorea.com / password'))

    def create_users(self):
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@kenyakorea.com',
                'first_name': 'Site', 'last_name': 'Administrator',
                'is_admin': True, 'is_staff': True, 'is_superuser': True,
            }
        )
        if created:
            admin.set_password('password')
            admin.save()
            self.stdout.write(f'  ✓ Admin user created: admin@kenyakorea.com / password')

        # Sample user
        user, created = User.objects.get_or_create(
            username='johndoe',
            defaults={'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'}
        )
        if created:
            user.set_password('password')
            user.save()
            self.stdout.write('  ✓ Sample user created: john@example.com / password')

    def create_site_settings(self):
        SiteSettings.objects.update_or_create(
            pk=1,
            defaults={
                # Identity
                'site_name': 'Kenya Community in Korea',
                'site_short_name': 'KCK',
                'tagline': 'Sote Pamoja — All Together',
                # Slogan
                'slogan': 'SOTE PAMOJA',
                'slogan_translation': 'All Together',
                'slogan_description': 'the spirit of our community',
                # Hero
                'hero_badge_text': 'Kenyan Community · Seoul · Korea',
                'hero_title': 'Kenya Community',
                'hero_title_accent': 'in Korea',
                'hero_subtitle': 'A community platform connecting, supporting and celebrating Kenyans across South Korea — events, embassy liaison, official communications, and a space that feels like home.',
                'hero_cta_primary_text': 'Join the Community',
                'hero_cta_secondary_text': 'Upcoming Events',
                # Embassy CTA
                'embassy_cta_eyebrow': 'Embassy Liaison Service',
                'embassy_cta_title': 'Need Embassy Services?',
                'embassy_cta_description': 'KCK helps Kenyans in Korea access embassy services through our community liaison program. Submit your request online and our officers will guide you through the process and coordinate with the Kenyan Embassy in Seoul on your behalf.',
                'embassy_cta_note': 'Note: Official processing and document issuance is done by the Embassy of Kenya — KCK is a community facilitator, not the embassy.',
                # Embassy disclaimer
                'embassy_disclaimer_enabled': True,
                'embassy_disclaimer_text': 'This is a community platform for Kenyans living in South Korea — not the official Kenya Embassy. For official embassy/consular services, please visit the Embassy of Kenya in Seoul.',
                # About
                'about_text': 'The Kenya Community in Korea (KCK) is a community organization for Kenyan citizens residing in or visiting South Korea.',
                'mission': 'To connect, serve, and support the Kenyan community in South Korea while promoting Kenyan culture and fostering goodwill between our two nations.',
                'vision': 'A thriving, connected Kenyan diaspora community in Korea that bridges the two nations through culture, business, and friendship.',
                # Footer
                'footer_about': 'Supporting and connecting the Kenyan community in South Korea through embassy liaison, cultural events, and community engagement.',
                # Contact
                'email': 'info@kenyakorea.com',
                'phone': '+82-2-XXXX-XXXX',
                'address': 'Seoul, South Korea',
                'office_hours': 'Monday - Friday: 9:00 AM - 5:00 PM',
                # Newsletter
                'newsletter_title': 'Subscribe to Newsletter',
                'newsletter_description': 'Get updates on community news, events, and announcements.',
                # Social
                'facebook_url': 'https://facebook.com/kck',
                'instagram_url': 'https://instagram.com/kck',
            }
        )
        self.stdout.write('  ✓ Site settings configured')

    def create_ambassador(self):
        AmbassadorProfile.objects.get_or_create(
            name='H.E. Ambassador Mwende Kamau',
            defaults={
                'title': 'Ambassador of Kenya to the Republic of Korea',
                'biography': 'Ambassador Mwende Kamau brings over 20 years of diplomatic experience to her role as Ambassador of Kenya to the Republic of Korea. She has previously served in diplomatic missions across Africa and Asia, and holds advanced degrees in International Relations and Public Administration.',
                'message': 'Karibu! It is my honor to welcome you to the Kenya Community in Korea. Our mission is to serve every Kenyan citizen in Korea with dedication, while strengthening the bonds of friendship between our two great nations. Whether you are here for tourism, business, study, or work, we are here to support you.',
                'email': 'ambassador@kenyakorea.com',
                'active': True,
            }
        )
        self.stdout.write('  ✓ Ambassador profile created')

    def create_visa_types(self):
        visa_data = [
            ('Tourist Visa', 'tourist', '🌍', 'For leisure travel, tourism, and short visits to Kenya. Perfect for exploring our beautiful country.',
             ['Valid passport (6+ months validity)', 'Completed application form', 'Passport-size photos (2)', 'Proof of accommodation', 'Return flight ticket', 'Bank statement (last 3 months)'],
             '5-10 business days', '$50'),
            ('Business Visa', 'business', '💼', 'For business meetings, conferences, and short-term business activities in Kenya.',
             ['Valid passport', 'Invitation letter from Kenyan business', 'Company registration documents', 'Business plan or agenda', 'Passport-size photos (2)', 'Bank statement'],
             '7-14 business days', '$100'),
            ('Student Visa', 'student', '🎓', 'For students accepted into academic programs at recognized Kenyan institutions.',
             ['Valid passport', 'Acceptance letter from Kenyan institution', 'Academic transcripts', 'Proof of financial support', 'Passport-size photos (2)', 'Medical certificate'],
             '10-15 business days', '$50'),
            ('Family/Visit Visa', 'family-visit', '👨‍👩‍👧', 'For visiting family members or attending personal events in Kenya.',
             ['Valid passport', 'Invitation letter from family member', 'Proof of relationship', 'Host ID copy', 'Passport-size photos (2)', 'Return flight ticket'],
             '5-10 business days', '$50'),
            ('Work Permit', 'work-permit', '🛠', 'For foreign nationals employed by Kenyan companies or organizations.',
             ['Valid passport', 'Employment contract', 'Employer registration documents', 'Academic/professional certificates', 'Passport-size photos (2)', 'Medical certificate', 'Police clearance certificate'],
             '15-30 business days', '$200'),
            ('Transit Visa', 'transit', '✈', 'For travelers passing through Kenya en route to another destination.',
             ['Valid passport', 'Confirmed onward ticket', 'Visa for destination country (if applicable)', 'Passport-size photos (2)'],
             '3-5 business days', '$20'),
        ]
        for i, (name, slug, icon, desc, reqs, time, fee) in enumerate(visa_data):
            VisaType.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'icon': icon, 'description': desc, 'requirements': reqs,
                         'processing_time': time, 'fee': fee, 'sort_order': i, 'active': True}
            )
        self.stdout.write(f'  ✓ {len(visa_data)} visa types created')

    def create_faqs(self):
        faqs_data = [
            ('general', 'How can I contact the embassy?', 'You can reach us by phone at +82-2-XXXX-XXXX, email at info@kenyakorea.com, or visit our office in Seoul during working hours (Mon-Fri, 9 AM - 5 PM).'),
            ('general', 'What are the office hours?', 'Our office is open Monday to Friday from 9:00 AM to 5:00 PM. We are closed on weekends and Korean public holidays.'),
            ('general', 'Where is the embassy located?', 'The Embassy of Kenya is located in Seoul, South Korea. Detailed directions are available on our Visit Us page.'),
            ('general', 'Do you provide translation services?', 'We offer basic English-Korean-Swahili assistance. For certified legal translations, we can recommend qualified professionals.'),
            ('visa', 'How long does visa processing take?', 'Processing times vary by visa type: Tourist visas take 5-10 business days, Business visas 7-14 days, Work permits 15-30 days.'),
            ('visa', 'Can I reapply if my visa is rejected?', 'Yes, you can reapply after addressing the reasons for rejection. We recommend contacting us to understand what documentation needs to be improved.'),
            ('visa', 'What documents are required for a visa?', 'Required documents vary by visa type. Generally you need a valid passport, application form, photos, and supporting documents specific to your visa category.'),
            ('visa', 'Can I track my visa application?', 'Yes, once you submit your application through our online portal, you can track its status in your dashboard at any time.'),
            ('visa', 'Is visa on arrival available in Kenya?', 'Visa on arrival is available for citizens of certain countries. We recommend checking with us in advance to confirm eligibility for your nationality.'),
            ('passport', 'How do I apply for a passport?', 'Kenyan citizens can apply for a passport through our online application form. You will need to provide your national ID, photos, and supporting documents.'),
            ('passport', 'How long does passport processing take?', 'Passport processing typically takes 2-4 weeks from submission. Expedited service may be available for emergencies.'),
            ('passport', 'What is the difference between renewal and new passport?', 'A renewal is for existing passports that have expired or are about to expire. A new passport application is for first-time applicants or those who have lost their passport.'),
            ('passport', 'What documents are required for passport application?', 'You need your Kenyan national ID, passport-size photos, your current or expired passport (for renewals), and proof of residence.'),
            ('consular', 'Do you provide document notarization?', 'Yes, we provide notarization services for various documents including affidavits, powers of attorney, and academic certificates.'),
            ('consular', 'What emergency services do you offer?', 'We provide 24/7 emergency assistance for Kenyan citizens in distress, including lost passport replacement, emergency travel documents, and welfare visits.'),
            ('consular', 'How do I register as a citizen abroad?', 'We encourage all Kenyan citizens in Korea to register with the embassy for emergency contact purposes. Registration can be done online through our website.'),
        ]
        for i, (cat, q, a) in enumerate(faqs_data):
            Faq.objects.update_or_create(
                question=q,
                defaults={'answer': a, 'category': cat, 'sort_order': i, 'active': True}
            )
        self.stdout.write(f'  ✓ {len(faqs_data)} FAQs created')

    def create_events(self):
        now = timezone.now()
        events_data = [
            ('Kenyan Independence Day Celebration (Madaraka Day)', now + timedelta(days=60), 'Annual celebration of Kenya\'s independence with music, food, and cultural performances.', 'Kenyan Embassy Hall, Seoul', 200, True),
            ('Community Cultural Night', now + timedelta(days=21), 'An evening of Kenyan music, dance, poetry, and storytelling showcasing our rich cultural heritage.', 'Itaewon Cultural Center, Seoul', 100, False),
            ('Consular Services Day', now + timedelta(days=30), 'Free consular services day for Kenyan citizens. Passport renewals, notarizations, and consultations.', 'Kenyan Embassy, Seoul', 50, False),
            ('Kenya-Korea Business Forum', now + timedelta(days=45), 'Networking event connecting Kenyan and Korean businesses for investment opportunities.', 'Grand Hyatt Seoul', 150, True),
            ('Kenyan Food Festival', now + timedelta(days=40), 'Taste authentic Kenyan cuisine including ugali, nyama choma, chapati, and more.', 'Gangnam Community Center', 300, True),
            ('Youth Mentorship Workshop', now + timedelta(days=28), 'Mentorship program connecting Kenyan youth in Korea with successful professionals.', 'Kenyan Embassy, Seoul', 30, False),
            ('Diaspora Investment Seminar', now - timedelta(days=15), 'Past event covering investment opportunities in Kenya for the diaspora community.', 'Online (Zoom)', 200, False),
            ('Swahili Language Class', now + timedelta(days=14), 'Weekly Swahili language classes for beginners.', 'KCK Community Center', 20, False),
        ]
        for title, date, desc, location, capacity, featured in events_data:
            Event.objects.update_or_create(
                title=title,
                defaults={'description': desc, 'date': date, 'location': location, 'capacity': capacity,
                        'registration_deadline': date - timedelta(days=3), 'active': True, 'featured': featured}
            )
        self.stdout.write(f'  ✓ {len(events_data)} events created')

    def create_news(self):
        admin = User.objects.filter(is_staff=True).first()
        news_data = [
            ('Embassy Launches New Visa Portal — What it Means for Kenyans in Korea',
             'The Embassy of Kenya in Seoul has launched a new online visa application portal. Here is what KCK members need to know.',
             'The Embassy of Kenya in Seoul has launched a new online visa application portal for Kenyans and foreign nationals applying from Korea. KCK is sharing this update with the community so members can take advantage of the improved process.\n\nWhat the new portal offers:\n• Online application submission without in-person queues for the first step\n• Digital document uploads\n• Real-time tracking of application status\n• Reduced processing times for complete applications\n\nHow KCK can help:\n• Our embassy liaison team can guide you through the application checklist\n• We can help you prepare documents before submission\n• For complex cases, we coordinate with embassy staff on your behalf\n\nTo request liaison support, visit the Embassy Liaison page on this site. All official approvals and document issuance remain with the Embassy of Kenya — KCK is a community facilitator, not the embassy.', True),
            ('Kenya-Korea Trade Relations Strengthen', 'Bilateral trade between Kenya and South Korea reaches new heights.',
             'Trade between Kenya and South Korea has reached a record high this year, with significant growth in technology, agriculture, and tourism sectors. The two nations continue to deepen their economic partnership through various collaborative initiatives.', False),
            ('Madaraka Day Celebration Announcement', 'Join us for the annual Madaraka Day celebration on June 1st.',
             'The Kenya Community in Korea invites all Kenyan citizens and friends of Kenya to join us for the annual Madaraka Day celebration. This year\'s event will feature traditional music, dance performances, Kenyan cuisine, and speeches from distinguished guests.', False),
            ('KCK Welcomes New Kenyan Ambassador to Korea',
             'The Kenya Community in Korea extends a warm welcome to H.E. Ambassador Mwende Kamau as she takes office in Seoul.',
             'The Kenya Community in Korea (KCK) warmly welcomes H.E. Ambassador Mwende Kamau, appointed by the Kenyan government as the new Ambassador of the Republic of Kenya to the Republic of Korea.\n\nOn behalf of all Kenyans living, working and studying across South Korea, KCK extends sincere congratulations to the Ambassador and her team. We look forward to a strong working relationship with the Embassy of Kenya in Seoul on matters affecting our community — from consular services to cultural exchange and trade facilitation.\n\nAs a community organisation, KCK will continue to liaise with the Embassy on behalf of our members and assist Kenyans in Korea in accessing official services. We congratulate the outgoing Ambassador on their service, and we look forward to welcoming Ambassador Kamau to upcoming KCK community events.\n\nNote: For official consular matters, please contact the Embassy of Kenya in Seoul directly. KCK is a community organisation, not the embassy.', False),
            ('Scholarship Opportunities for Kenyan Students', 'New scholarship programs available for Kenyan students in Korea.',
             'We are pleased to announce several new scholarship opportunities available for Kenyan students pursuing higher education in South Korea. These scholarships cover tuition, living expenses, and Korean language training.', False),
        ]
        for i, (title, excerpt, content, featured) in enumerate(news_data):
            News.objects.update_or_create(
                title=title,
                defaults={'excerpt': excerpt, 'content': content, 'author': admin, 'published': True, 'featured': featured}
            )
        self.stdout.write(f'  ✓ {len(news_data)} news articles created')

    def create_testimonials(self):
        testimonials_data = [
            ('Sarah Wanjiru', 'Graduate Student, Seoul National University', 'The KCK has been instrumental in helping me navigate life as a Kenyan student in Korea. From visa support to cultural events, they provide a home away from home.'),
            ('James Otieno', 'Business Owner', 'Thanks to the embassy\'s support, I was able to expand my business between Nairobi and Seoul. Their consular services are efficient and reliable.'),
            ('Grace Njeri', 'Tourist', 'Applied for a tourist visa and was amazed at how smooth the process was. The online portal made everything easy!'),
            ('Michael Kimani', 'IT Professional', 'Working in Korea as a Kenyan, KCK events help me stay connected with my roots. The community is amazing!'),
            ('Dr. Faith Akinyi', 'Medical Professional', 'The embassy provided excellent support during an emergency. Their 24/7 consular services truly make a difference.'),
            ('Peter Mwangi', 'Student', 'KCK mentorship programs helped me build my career network in Korea. I highly recommend getting involved!'),
        ]
        for name, role, msg in testimonials_data:
            Testimonial.objects.get_or_create(name=name, defaults={'role': role, 'message': msg, 'active': True})
        self.stdout.write(f'  ✓ {len(testimonials_data)} testimonials created')

    def create_announcements(self):
        now = timezone.now()
        Announcement.objects.get_or_create(
            title='Welcome',
            defaults={'message': 'Welcome to the new KCK website! Register for an account to access online services.',
                     'level': 'info', 'active': True,
                     'starts_at': now - timedelta(days=1), 'ends_at': now + timedelta(days=30)}
        )
        self.stdout.write('  ✓ Announcements created')

    def create_pages(self):
        pages_data = [
            ('welcome-message', 'Welcome Message', '<p>Welcome to the Kenya Community in Korea...</p>'),
            ('embassy-services', 'Embassy Services', '<p>Our embassy offers a wide range of services to Kenyan citizens and visitors...</p>'),
        ]
        for slug, title, content in pages_data:
            Page.objects.update_or_create(slug=slug, defaults={'title': title, 'content': content, 'active': True})
        self.stdout.write(f'  ✓ {len(pages_data)} pages created')

    def create_contact_messages(self):
        messages_data = [
            ('Alex Ochieng', 'alex@example.com', 'Visa inquiry', 'I would like to know more about the business visa requirements.', False),
            ('Mary Wambui', 'mary@example.com', 'Thank you', 'Thank you for the great service with my passport renewal.', True),
            ('David Kipchoge', 'david@example.com', 'Event question', 'Will there be transportation provided for the Madaraka Day event?', False),
        ]
        for name, email, subject, message, is_read in messages_data:
            ContactMessage.objects.get_or_create(
                email=email, subject=subject,
                defaults={'name': name, 'message': message, 'is_read': is_read}
            )
        self.stdout.write(f'  ✓ {len(messages_data)} contact messages created')

    def create_leaders(self):
        leader_data = [
            ('president', 'president', 'president@kenyakorea.com', 'James', 'Mwangi', 'President of KCK',
             'James has served in leadership roles across the Kenyan community in Asia for over 15 years. He leads KCK with dedication and vision, committed to strengthening community bonds among Kenyans in Korea.'),
            ('vice_president', 'vice_president', 'vice@kenyakorea.com', 'Grace', 'Wanjiku', 'Vice President',
             'Grace supports the president in all strategic initiatives and oversees membership engagement across different Korean cities.'),
            ('secretary', 'secgen', 'secgen@kenyakorea.com', 'Peter', 'Kamau', 'Secretary General',
             'As Secretary General, Peter manages community records, documentation, official correspondence and member verification. He keeps our community organised and informed.'),
            ('treasurer', 'treasurer', 'treasurer@kenyakorea.com', 'Faith', 'Akinyi', 'Community Treasurer',
             'Faith oversees all financial matters and ensures transparent management of community funds and membership fees.'),
            ('welfare', 'welfare', 'welfare@kenyakorea.com', 'David', 'Ochieng', 'Welfare Officer',
             'David coordinates welfare support for community members during emergencies, bereavements, celebrations, and times of need.'),
            ('committee', 'committee_mary', 'committee1@kenyakorea.com', 'Mary', 'Wambui', 'Committee Member - Events',
             'Mary serves on the events and cultural activities committee, organizing regular cultural gatherings.'),
        ]

        for i, (role, username, email, fname, lname, title, bio) in enumerate(leader_data):
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email, 'first_name': fname, 'last_name': lname,
                    'is_verified': True, 'email_verified': True,
                }
            )
            # Always ensure password is set correctly
            user.set_password('password')
            user.save()

            Leader.objects.update_or_create(
                user=user,
                defaults={
                    'role': role, 'title': title, 'bio': bio,
                    'email_official': email, 'sort_order': i, 'is_active': True,
                    'appointed_at': timezone.now().date() - timedelta(days=365),
                    'term_ends': timezone.now().date() + timedelta(days=365),
                }
            )
        self.stdout.write(f'  ✓ {len(leader_data)} leaders created')

    def create_certificates(self):
        chairman = Leader.objects.filter(role='president').first()
        welfare = Leader.objects.filter(role='welfare').first()
        sample_user = User.objects.filter(username='johndoe').first()

        cert_data = [
            {
                'recipient_name': 'John Doe', 'recipient_user': sample_user,
                'cert_type': 'participation',
                'body': 'For active participation in the Kenya Community in Korea cultural celebration and dedicated contribution to community events throughout the year 2026.',
                'event_title': 'Madaraka Day Celebration 2026',
                'issued_by': chairman, 'status': 'draft',
            },
            {
                'recipient_name': 'Sarah Wanjiru', 'cert_type': 'appreciation',
                'body': 'In recognition of outstanding volunteer service and dedication to supporting new arrivals in the Kenyan community in Korea.',
                'issued_by': welfare, 'status': 'draft',
            },
            {
                'recipient_name': 'Michael Kimani', 'cert_type': 'leadership',
                'body': 'For exemplary leadership in organizing the Kenya-Korea Business Forum 2026 and fostering professional networking within our community.',
                'event_title': 'Kenya-Korea Business Forum 2026',
                'issued_by': chairman, 'status': 'draft',
            },
        ]

        for data in cert_data:
            Certificate.objects.get_or_create(
                recipient_name=data['recipient_name'], cert_type=data['cert_type'],
                defaults=data
            )
        self.stdout.write(f'  ✓ {len(cert_data)} certificates created (as drafts)')

    def create_communications(self):
        chairman = Leader.objects.filter(role='president').first()
        welfare = Leader.objects.filter(role='welfare').first()
        secretary = Leader.objects.filter(role='secretary').first()

        comm_data = [
            {
                'subject': 'Welcome to the New KCK Platform',
                'body': ('Dear community members,\n\nIt is with great pleasure that I welcome you to our new digital community platform. '
                         'This website represents a significant step forward in how we connect, communicate, and support one another as Kenyans living in South Korea.\n\n'
                         'Through this platform, you will be able to register as community members, receive official communications, '
                         'register for events, and obtain official certificates of recognition for your contributions.\n\n'
                         'Together, let us continue to build a vibrant and supportive community.'),
                'category': 'general', 'audience': 'all',
                'sender': chairman, 'status': 'draft',
            },
            {
                'subject': 'Annual General Meeting Notice',
                'body': ('Dear members,\n\nThis is to formally notify all registered members of the Kenya Community in Korea about the upcoming Annual General Meeting.\n\n'
                         'The AGM will cover: financial reports, new elections for committee positions, amendments to the community constitution, and the year-ahead planning.\n\n'
                         'All members are strongly encouraged to attend. Details about the venue and agenda will follow shortly.'),
                'category': 'general', 'audience': 'members',
                'sender': secretary, 'status': 'draft',
            },
            {
                'subject': 'Community Welfare Support Programme',
                'body': ('Dear community,\n\nWe are pleased to announce the launch of our expanded welfare support programme for Kenyan citizens in Korea facing emergencies, medical challenges, or bereavement.\n\n'
                         'Members in need of support can reach out confidentially to the welfare office. All requests are handled with discretion and compassion.'),
                'category': 'welfare', 'audience': 'all',
                'sender': welfare, 'status': 'draft',
            },
        ]

        for data in comm_data:
            Communication.objects.get_or_create(subject=data['subject'], defaults=data)
        self.stdout.write(f'  ✓ {len(comm_data)} communications created')

    def create_comm_announcements(self):
        ann_data = [
            ('Welcome to Our New Website', 'We are excited to launch our new community platform with enhanced features for members.',
             ('We are thrilled to announce the launch of our redesigned community platform! '
              'The new website features online certificate verification, official communications, event registration, leader directory, and much more.\n\n'
              'Register an account today to access member-only features and stay connected with the community.'),
             'general', True, True),
            ('Madaraka Day 2026 - Save the Date', 'Annual Independence Day celebration scheduled for June 1st, 2026.',
             ('Mark your calendars! The Kenya Community in Korea will be hosting the annual Madaraka Day celebration on June 1st, 2026. '
              'Details about venue, program, and registration will follow in the coming weeks.\n\n'
              'This year promises to be our biggest celebration yet with Kenyan food, music, dance performances, and distinguished guests.'),
             'celebration', True, False),
            ('Community Condolences', 'Our condolences to the Mwangi family on their recent loss.',
             ('The Kenya Community in Korea extends heartfelt condolences to the Mwangi family on the passing of their beloved mother. '
              'Our thoughts and prayers are with the family during this difficult time.\n\n'
              'Members wishing to contribute to welfare support for the family can contact the welfare office.'),
             'condolence', True, False),
            ('New Swahili Classes Starting', 'Weekly Swahili language classes begin this month.',
             ('Beginner and intermediate Swahili language classes will start this month. Open to both Kenyans wanting to maintain their language skills and Koreans interested in learning.\n\n'
              'Classes will be held every Saturday at the KCK community center.'),
             'event', True, False),
        ]
        for i, (title, excerpt, body, cat, pub, pin) in enumerate(ann_data):
            CommAnnouncement.objects.get_or_create(
                title=title,
                defaults={
                    'excerpt': excerpt, 'body': body, 'category': cat,
                    'is_published': pub, 'is_pinned': pin,
                    'published_at': timezone.now() - timedelta(days=i),
                }
            )
        self.stdout.write(f'  ✓ {len(ann_data)} community announcements created')

    def create_service_guides(self):
        guides_data = [
            ('passport_new', 'New Passport Application', '📘',
             'Apply for a new Kenyan passport if you are a Kenyan citizen who has never held a Kenyan passport before, or whose previous passport expired more than 5 years ago.',
             ['Valid Kenyan National ID (original + copy)', 'Birth certificate', 'Recent passport-size photos (4, white background)',
              'Proof of Korean residence (ARC card copy)', 'Completed passport application form',
              'Proof of payment of embassy fees'],
             '4-8 weeks from embassy submission', 'USD 70 (embassy fee, subject to change)', 'Free'),
            ('passport_renewal', 'Passport Renewal', '♻️',
             'Renew an existing Kenyan passport that is about to expire (within 6 months) or has recently expired.',
             ['Current/expired Kenyan passport (original + copy)', 'Valid Kenyan National ID',
              'Recent passport-size photos (4)', 'Proof of Korean residence', 'Completed renewal form',
              'Payment of renewal fees'],
             '3-6 weeks', 'USD 60 (embassy fee)', 'Free'),
            ('passport_replacement', 'Passport Replacement (Lost/Damaged)', '🆘',
             'Replace a Kenyan passport that has been lost, stolen, or damaged. Requires police report.',
             ['Police report (from Korean police station)', 'Sworn affidavit of loss', 'Kenyan National ID',
              'Passport-size photos (4)', 'Proof of identity (any Kenyan document)', 'Payment of replacement fees'],
             '6-10 weeks', 'USD 100 (embassy fee)', 'Free'),
            ('emergency_travel', 'Emergency Travel Document (ETD)', '🚨',
             'Obtain an emergency travel document if you need to travel urgently and do not have a valid passport.',
             ['Proof of emergency (medical, bereavement, etc.)', 'Kenyan National ID or any proof of Kenyan citizenship',
              'Passport-size photos (2)', 'Travel itinerary', 'Statement explaining the emergency'],
             '1-3 business days (expedited)', 'USD 50 (embassy fee)', 'Free'),
            ('national_id', 'National ID Application / Renewal', '🪪',
             'Apply for a new Kenyan National ID card or renew an existing one through the embassy.',
             ['Birth certificate (original + copy)', 'Parents\' IDs or death certificates if deceased',
              'Passport-size photos (2)', 'Proof of residence in Korea', 'Previous ID (for renewals)'],
             '6-12 weeks', 'USD 10 (embassy fee)', 'Free'),
            ('birth_certificate', 'Birth Certificate Application', '👶',
             'Obtain or register a birth certificate for children born in Korea to Kenyan parents, or obtain a Kenyan birth certificate for yourself.',
             ['Korean birth certificate (with apostille/authentication)', 'Parents\' Kenyan IDs/passports',
              'Marriage certificate of parents (if applicable)', 'Completed registration form'],
             '4-8 weeks', 'USD 20 (embassy fee)', 'Free'),
            ('notarization', 'Document Notarization / Authentication', '📜',
             'Have documents notarized or authenticated by the embassy for use in Kenya (academic certificates, legal documents, affidavits, etc.).',
             ['Original document to be notarized', 'Copy of your ID/passport', 'Purpose of notarization stated in writing'],
             '3-7 business days', 'USD 30 per document', 'Free'),
            ('citizen_registration', 'Citizen Registration (Diaspora)', '🌍',
             'Register as a Kenyan citizen living abroad. Highly recommended for all Kenyans in Korea for emergency contact, consular assistance, and voting rights.',
             ['Kenyan passport or National ID', 'Proof of residence in Korea (ARC)',
              'Emergency contact information', 'Completed registration form'],
             '1-2 weeks', 'Free', 'Free'),
            ('consular_letter', 'Consular Letter Request', '✉️',
             'Request an official consular letter from the embassy for bank account opening, visa applications to third countries, legal matters, and more.',
             ['Purpose of the letter (stated clearly)', 'Supporting documents relevant to the purpose',
              'Valid Kenyan ID/passport', 'Korean residence proof'],
             '5-10 business days', 'USD 25 per letter', 'Free'),
            ('visa_kenya', 'Kenya Visa Information / Guidance', '🛂',
             'Get guidance on obtaining visas for travel to Kenya. The embassy processes visa applications for non-Kenyan citizens wishing to travel to Kenya.',
             ['Valid passport (6+ months validity)', 'Purpose of travel', 'Accommodation proof in Kenya',
              'Return ticket', 'Bank statement (3 months)'],
             '5-15 business days', 'Varies by visa type (USD 20-200)', 'Free'),
            ('appointment_booking', 'Embassy Appointment Booking Assistance', '📅',
             'Need help booking an appointment at the Kenyan Embassy in Seoul? KCK can help coordinate your appointment schedule.',
             ['Preferred dates and times', 'Purpose of the appointment',
              'Any prior reference numbers from the embassy'],
             '2-5 business days to confirm', 'No embassy fee for appointments', 'Free'),
            ('other', 'Other Embassy Service', '🔖',
             'Any other embassy-related service not listed. Describe your need in detail and a KCK officer will guide you.',
             ['Description of the service needed', 'Any relevant supporting documents'],
             'Varies', 'Varies', 'Free'),
        ]
        for i, (stype, title, icon, desc, reqs, timeline, efee, kfee) in enumerate(guides_data):
            ServiceGuide.objects.update_or_create(
                service_type=stype,
                defaults={
                    'title': title, 'icon': icon, 'description': desc,
                    'requirements': reqs, 'typical_timeline': timeline,
                    'embassy_fee': efee, 'kck_facilitation_fee': kfee,
                    'sort_order': i, 'active': True,
                }
            )
        self.stdout.write(f'  ✓ {len(guides_data)} service guides created')

    def create_sports_data(self):
        # Sports
        sports_data = [
            ('Football', 'football', '⚽', 'The beautiful game — community 11-a-side matches and friendly games.', 0),
            ('Rugby', 'rugby', '🏉', 'Rugby union for Kenyans in Korea — training and matches.', 1),
            ('Athletics', 'athletics', '🏃', 'Track and field, short and long distance, jumps and throws.', 2),
            ('Basketball', 'basketball', '🏀', 'Community basketball leagues and pickup games.', 3),
            ('Volleyball', 'volleyball', '🏐', 'Indoor and beach volleyball for the community.', 4),
            ('Marathon', 'marathon', '🏅', 'Marathon and long-distance running — we love distance!', 5),
        ]
        sports = {}
        for name, cat, icon, desc, order in sports_data:
            s, _ = Sport.objects.update_or_create(
                name=name,
                defaults={'category': cat, 'icon': icon, 'description': desc,
                          'sort_order': order, 'active': True}
            )
            sports[cat] = s

        # The Kenyan community team (ONE team representing Kenyans in Korea per sport).
        # External opponent clubs are added separately so fixtures look realistic.
        teams_data = [
            # Kenyan team — the ONE KCK team per sport
            ('football',   'KCK FC',              'KCK',  '#C8102E', '#008751', 'Seoul World Cup Stadium Annex', True),
            ('rugby',      'KCK Rugby',           'KCK',  '#C8102E', '#000000', 'Hannam Rugby Field',            True),
            ('basketball', 'KCK Basketball',      'KCK',  '#C8102E', '#FFD700', 'Gangnam Gym',                   True),
            ('volleyball', 'KCK Volleyball',      'KCK',  '#C8102E', '#008751', 'Itaewon Indoor Arena',          True),
            ('athletics',  'KCK Athletics',       'KCK',  '#C8102E', '#FFD700', 'Olympic Park Track',            True),
            ('marathon',   'KCK Runners',         'KCK',  '#C8102E', '#000000', 'Han River Park',                True),

            # External opponents (Korean / international clubs KCK plays against)
            ('football',   'Seoul United',        'SEL',  '#1E88E5', '#FFFFFF', 'Seoul City Ground',             False),
            ('football',   'Busan Dragons',       'BSN',  '#FF6D00', '#000000', 'Busan Sports Complex',          False),
            ('football',   'Incheon Tigers',      'INC',  '#2E7D32', '#FFFFFF', 'Incheon Stadium',               False),
            ('rugby',      'Seoul Rugby Club',    'SRC',  '#1565C0', '#FFFFFF', 'Yongsan Rugby Park',            False),
        ]
        teams = {}
        for sport_key, name, short, c1, c2, venue, _is_kenyan in teams_data:
            if sport_key not in sports:
                continue
            t, _ = Team.objects.update_or_create(
                name=name,
                defaults={'sport': sports[sport_key], 'short_name': short,
                          'color_primary': c1, 'color_secondary': c2,
                          'home_venue': venue, 'active': True}
            )
            teams[name] = t

        # Squad — players only for the Kenyan community teams
        player_names = {
            'KCK FC': [
                (1,  'Daniel Otieno',    'gk',  True),
                (4,  'Joseph Okumu',     'df',  False),
                (5,  'Brian Kimani',     'df',  False),
                (8,  'James Mwangi Jr.', 'mf',  False),
                (10, 'Victor Wanyama',   'mf',  False),
                (11, 'Michael Olunga',   'fw',  False),
                (9,  'Ayub Timbe',       'fw',  False),
            ],
            'KCK Rugby': [
                (10, 'Dennis Ombachi',   'fw', True),
                (9,  'Collins Injera',   'fw', False),
                (7,  'Oscar Ouma',       'mf', False),
            ],
            'KCK Basketball': [
                (23, 'Tyler Ongwae',     'f',  True),
                (10, 'Victor Bosire',    'g',  False),
            ],
            'KCK Volleyball': [
                (12, 'Mercy Moim',       'any', True),
            ],
            'KCK Athletics': [
                (1,  'Hellen Obiri',     'any', True),
                (2,  'Eliud Kipchoge',   'any', False),
            ],
            'KCK Runners': [
                (1,  'Brigid Kosgei',    'any', True),
            ],
        }
        player_count = 0
        for team_name, roster in player_names.items():
            if team_name not in teams:
                continue
            for num, name, pos, captain in roster:
                Player.objects.update_or_create(
                    team=teams[team_name], full_name=name,
                    defaults={'jersey_number': num, 'position': pos,
                              'is_captain': captain, 'is_active': True}
                )
                player_count += 1

        # Friendly fixtures — KCK vs external Korean clubs
        fixture_data = []
        if 'football' in sports:
            fixture_data = [
                # Past (completed results)
                ('KCK FC',         'Seoul United',   -14, 'completed', 2, 1, 'Seoul World Cup Stadium Annex'),
                ('Busan Dragons',  'KCK FC',         -7,  'completed', 1, 3, 'Busan Sports Complex'),
                ('KCK FC',         'Incheon Tigers', -3,  'completed', 1, 1, 'Seoul World Cup Stadium Annex'),
                # Upcoming
                ('KCK FC',         'Busan Dragons',  7,   'scheduled', None, None, 'Seoul World Cup Stadium Annex'),
                ('Incheon Tigers', 'KCK FC',         14,  'scheduled', None, None, 'Incheon Stadium'),
                ('Seoul United',   'KCK FC',         21,  'scheduled', None, None, 'Seoul City Ground'),
            ]
            for home, away, days, status, h_score, a_score, venue in fixture_data:
                if home not in teams or away not in teams:
                    continue
                kickoff = timezone.now() + timedelta(days=days, hours=15)
                Fixture.objects.update_or_create(
                    home_team=teams[home], away_team=teams[away],
                    kickoff=kickoff,
                    defaults={'venue': venue, 'status': status,
                              'home_score': h_score, 'away_score': a_score}
                )

        # Sports events
        events_data = [
            ('KCK Community Sports Day 2026', 'sports_day', 'football',
             'Annual community sports day featuring football, athletics, and fun games for all ages.',
             timezone.now() + timedelta(days=30), 'Olympic Park Seoul'),
            ('Weekly Football Training', 'training', 'football',
             'Open training session for all KCK football players — bring your boots!',
             timezone.now() + timedelta(days=3, hours=18), 'Hannam Football Field'),
            ('Seoul Marathon Team Meet', 'meet', 'marathon',
             'Monthly meet for the KCK marathon squad — long run + post-run brunch.',
             timezone.now() + timedelta(days=10), 'Han River Park'),
        ]
        for title, etype, sport_key, desc, starts, venue in events_data:
            SportsEvent.objects.update_or_create(
                title=title,
                defaults={'event_type': etype, 'sport': sports.get(sport_key),
                          'description': desc, 'starts_at': starts, 'venue': venue,
                          'registration_open': True, 'active': True}
            )

        # Sports news
        news_data = [
            ('KCK FC beat Seoul United 2-1 in friendly opener',
             'A strong start to the season for the KCK FC against local opposition.',
             'KCK FC — the Kenyan community team in Korea — got their friendly season off to a flying start with a 2-1 win over Seoul United at the Seoul World Cup Stadium Annex this weekend. '
             'Goals from Michael Olunga and Victor Wanyama secured the victory in front of a strong community turnout.\n\n'
             'Captain and goalkeeper Daniel Otieno praised the squad\'s discipline and said the team is looking forward to more friendlies against local Korean clubs this season.',
             True, 'football'),
            ('KCK Rugby to host friendly against Seoul Rugby Club',
             'An exciting friendly match is scheduled for next month.',
             'KCK Rugby have announced a friendly fixture against Seoul Rugby Club, to be played at Hannam Rugby Field. '
             'This is a great chance for community members to come out and support the Kenyan rugby team here in Korea.',
             False, 'rugby'),
            ('Community Sports Day 2026 — Save the date!',
             'Our annual sports day returns in May — fun for the whole family.',
             'Mark your calendars! KCK Community Sports Day 2026 will take place at Olympic Park Seoul. '
             'Events include football matches, athletics races, volleyball, fun games for children, and cultural performances.\n\n'
             'Registration is now open for individual participants and community members who want to volunteer.',
             False, 'football'),
        ]
        for title, excerpt, content, featured, sport_key in news_data:
            SportsNews.objects.update_or_create(
                title=title,
                defaults={'excerpt': excerpt, 'content': content, 'featured': featured,
                          'published': True, 'related_sport': sports.get(sport_key)}
            )

        kck_team_count = sum(1 for n in teams if n.startswith('KCK '))
        self.stdout.write(
            f'  ✓ Sports seeded: {len(sports)} sports, '
            f'{kck_team_count} KCK teams + {len(teams) - kck_team_count} opponent clubs, '
            f'{player_count} players, {len(fixture_data)} fixtures'
        )

    def create_market_categories(self):
        """Seed default marketplace categories."""
        categories_data = [
            ('Food & Groceries', '🛒', 'Kenyan foodstuffs, spices, flours, beverages, snacks', 1),
            ('Clothing & Fashion', '👗', 'African prints, ankara, kitenge, handmade fashion', 2),
            ('Beauty & Hair', '💇', 'Hair products, cosmetics, hair braiding, salon services', 3),
            ('Jewellery & Accessories', '💍', 'Beaded jewellery, African accessories, watches', 4),
            ('Art & Crafts', '🎨', 'Paintings, sculptures, woodwork, soapstone, handicraft', 5),
            ('Home & Decor', '🏠', 'Traditional decor, African prints for home, baskets', 6),
            ('Services', '🧰', 'Translation, tutoring, photography, event planning', 7),
            ('Electronics', '📱', 'Phones, gadgets, accessories', 8),
            ('Books & Media', '📚', 'Books, music, films from Kenya and Africa', 9),
            ('Other', '📦', 'Anything else not covered above', 99),
        ]
        for name, icon, desc, order in categories_data:
            ProductCategory.objects.update_or_create(
                name=name,
                defaults={'icon': icon, 'description': desc, 'sort_order': order, 'active': True}
            )
        self.stdout.write(f'  ✓ {len(categories_data)} market categories created')

    def create_discover_content(self):
        """Seed Discover Kenya attractions + travel essentials."""
        attractions = [
            ('Maasai Mara', 'bi-tree', True, 1,
             'World-famous for the Great Migration, where millions of wildebeest, zebra, and gazelle traverse the Mara River in one of nature\'s greatest spectacles.'),
            ('Mount Kenya', 'bi-triangle', False, 2,
             'Africa\'s second-highest peak offers stunning hiking routes, alpine landscapes, and deep spiritual significance to many Kenyan communities.'),
            ('Diani Beach', 'bi-sun', True, 3,
             'Pristine white sand beaches along the Indian Ocean — perfect for swimming, snorkelling, kite surfing, and simply relaxing.'),
            ('Lake Nakuru', 'bi-water', False, 4,
             'Famed for its flamboyance of flamingos and abundant wildlife including rhinos, lions, and leopards in a stunning Rift Valley setting.'),
            ('Nairobi', 'bi-building', False, 5,
             'The vibrant capital blends modern city life with wildlife at Nairobi National Park, rich museums, and a thriving arts and food scene.'),
            ('Lamu Island', 'bi-compass', True, 6,
             'A UNESCO World Heritage Site preserving centuries-old Swahili culture, architecture, and a beautifully tranquil pace of life.'),
            ('Amboseli National Park', 'bi-camera', False, 7,
             'Home to large elephant herds set against the iconic backdrop of Mount Kilimanjaro — one of the most photographed parks in Africa.'),
            ('Tsavo National Parks', 'bi-map', False, 8,
             'One of the largest wildlife sanctuaries on the continent — red elephants, vast savannahs, and the legendary Mzima Springs.'),
        ]
        for title, icon, featured, order, desc in attractions:
            DiscoverAttraction.objects.update_or_create(
                title=title,
                defaults={'icon': icon, 'featured': featured, 'sort_order': order,
                          'short_description': desc, 'active': True}
            )

        essentials = [
            ('Currency', 'Kenyan Shilling (KES)', 'bi-currency-exchange', 1),
            ('Languages', 'Swahili & English', 'bi-translate', 2),
            ('Climate', 'Tropical · Varies by region', 'bi-thermometer-sun', 3),
            ('Power', '240V · Type G plugs', 'bi-plug', 4),
            ('Time Zone', 'East Africa Time (UTC+3)', 'bi-clock', 5),
            ('Dialing Code', '+254', 'bi-telephone', 6),
            ('Best Time to Visit', 'Jul–Oct & Dec–Mar', 'bi-calendar-check', 7),
            ('Visa Required', 'Yes — eVisa available', 'bi-passport', 8),
        ]
        for title, value, icon, order in essentials:
            TravelEssential.objects.update_or_create(
                title=title,
                defaults={'value': value, 'icon': icon, 'sort_order': order, 'active': True}
            )

        self.stdout.write(f'  ✓ {len(attractions)} attractions + {len(essentials)} travel essentials created')
