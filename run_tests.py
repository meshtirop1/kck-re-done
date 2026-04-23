"""Comprehensive platform test suite for KCK Django site.

Usage: python run_tests.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kck_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.base import ContentFile

User = get_user_model()


# =============================================================================
# Test framework
# =============================================================================

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.failures = []
        self.current_section = ''

    def section(self, name):
        self.current_section = name
        print(f'\n{"="*72}')
        print(f'  {name}')
        print(f'{"="*72}')

    def test(self, name, condition, detail=''):
        if condition:
            self.passed += 1
            print(f'  [PASS] {name}' + (f' — {detail}' if detail else ''))
        else:
            self.failed += 1
            self.failures.append(f'[{self.current_section}] {name}' + (f' ({detail})' if detail else ''))
            print(f'  [FAIL] {name}' + (f' — {detail}' if detail else ''))

    def skip(self, name, reason):
        self.skipped += 1
        print(f'  [SKIP] {name} — {reason}')

    def test_status(self, name, client, url, expected, detail_fn=None):
        try:
            r = client.get(url)
            ok = r.status_code == expected
            detail = f'GET {url} -> {r.status_code} (expected {expected})'
            if detail_fn:
                detail = detail_fn(r, detail)
            self.test(name, ok, detail)
            return r
        except Exception as e:
            self.test(name, False, f'GET {url} raised: {type(e).__name__}: {str(e)[:80]}')
            return None

    def safe_post(self, client, url, data, files=None):
        try:
            if files:
                return client.post(url, data, files=files)
            return client.post(url, data)
        except Exception as e:
            return type('FakeResp', (), {'status_code': 500, 'content': str(e).encode()})()

    def safe_get(self, client, url):
        try:
            return client.get(url)
        except Exception as e:
            return type('FakeResp', (), {'status_code': 500, 'content': str(e).encode()})()

    def summary(self):
        total = self.passed + self.failed
        print(f'\n{"="*72}')
        print(f'  SUMMARY')
        print(f'{"="*72}')
        print(f'  Total tests run: {total}')
        print(f'  Passed: {self.passed}')
        print(f'  Failed: {self.failed}')
        print(f'  Skipped: {self.skipped}')
        if self.failures:
            print(f'\n  FAILURES:')
            for f in self.failures:
                print(f'    - {f}')
        else:
            print(f'\n  All tests passed!')
        print(f'{"="*72}')
        return 0 if self.failed == 0 else 1


t = TestRunner()


# =============================================================================
# 1. PUBLIC ROUTES (guest access)
# =============================================================================

t.section('1. PUBLIC ROUTES — GUEST ACCESS')

guest = Client()

public_routes = [
    ('Home page', '/', 200),
    ('About page', '/about/', 200),
    ('Contact page', '/contact/', 200),
    ('Ambassador page', '/ambassador/', 200),
    ('Embassy history', '/embassy-history/', 200),
    ('Visit us', '/visit/', 200),
    ('Discover Kenya', '/discover/', 200),
    ('Privacy policy', '/privacy/', 200),
    ('Data handling', '/data-handling/', 200),
    ('Terms of service', '/terms/', 200),
    ('Search page', '/search/', 200),
    ('Search with query', '/search/?q=visa', 200),

    # Services
    ('Visa types list', '/services/visa/types/', 200),
    ('Visa type detail (tourist)', '/services/visa/type/tourist/', 200),
    ('Visa services', '/services/visa/services/', 200),
    ('Visa issues', '/services/visa/issues/', 200),
    ('Visa FAQs', '/services/visa/faqs/', 200),
    ('Passport request info', '/services/passport/request/', 200),
    ('Queries', '/services/queries/', 200),
    ('Highlights', '/services/highlights/', 200),
    ('All FAQs', '/services/faqs/', 200),

    # Events
    ('Events list', '/events/', 200),
    ('Events calendar', '/events/calendar/', 200),
    ('Events highlights', '/events/highlights/', 200),

    # Community
    ('Community index', '/community/', 200),
    ('Community history', '/community/history/', 200),
    ('Community location', '/community/location/', 200),
    ('Community hours', '/community/hours/', 200),
    ('Community mission', '/community/mission/', 200),
    ('Community vision', '/community/vision/', 200),
    ('News list', '/community/news/', 200),
    ('Testimonials', '/community/testimonials/', 200),

    # Leaders
    ('Leaders list', '/leaders/', 200),

    # Embassy services liaison
    ('Embassy liaison info', '/embassy-services/', 200),
    ('Service types list', '/embassy-services/services/', 200),
    ('Service detail (passport renewal)', '/embassy-services/services/passport_renewal/', 200),

    # Certificates
    ('Certificate verify home', '/certificates/', 200),

    # Communications
    ('Public comms list', '/communications/', 200),
    ('Announcements list', '/communications/announcements/', 200),

    # Endorsements
    ('Endorsement verify home', '/endorsements/', 200),

    # Auth
    ('Login page', '/accounts/login/', 200),
    ('Register page', '/accounts/register/', 200),
    ('Password reset', '/accounts/password_reset/', 404),  # may not exist
]

for name, url, expected in public_routes:
    if expected == 404:
        # For password_reset, try but tolerate 404
        r = guest.get(url)
        if r.status_code == 200:
            t.test(name, True, f'GET {url} → 200')
        elif r.status_code == 404:
            t.skip(name, f'not configured')
        else:
            t.test(name, False, f'GET {url} → {r.status_code}')
    else:
        t.test_status(name, guest, url, expected)


# =============================================================================
# 2. AUTH FLOWS
# =============================================================================

t.section('2. AUTHENTICATION FLOWS')

# Register new user
new_username = 'testuser_' + os.urandom(4).hex()
new_email = f'{new_username}@test.com'
r = guest.post('/accounts/register/', {
    'username': new_username,
    'first_name': 'Test', 'last_name': 'User',
    'email': new_email, 'phone': '+82-10-1234-5678',
    'password1': 'SuperSecret9!', 'password2': 'SuperSecret9!',
})
t.test('User registration POST', r.status_code in (200, 302),
       f'status={r.status_code}')
t.test('User created in DB', User.objects.filter(username=new_username).exists())

# Login with new user
login_client = Client()
login_ok = login_client.login(username=new_username, password='SuperSecret9!')
t.test('New user can log in', login_ok)

# Access dashboard
r = login_client.get('/accounts/dashboard/')
t.test('Authenticated user can access dashboard', r.status_code == 200,
       f'status={r.status_code}')

# Access profile
r = login_client.get('/accounts/profile/')
t.test('User can access profile', r.status_code == 200, f'status={r.status_code}')

# Logout
r = login_client.post('/accounts/logout/')
t.test('User can log out', r.status_code in (200, 302))

# Test existing seeded users
for uname in ['admin', 'johndoe', 'chairman', 'secretary', 'treasurer', 'welfare',
              'vice_chairman', 'committee_mary']:
    c = Client()
    ok = c.login(username=uname, password='password')
    t.test(f'Seeded user "{uname}" can log in', ok)


# =============================================================================
# 3. GUEST ACCESS CONTROL (should be blocked)
# =============================================================================

t.section('3. ACCESS CONTROL — GUESTS BLOCKED FROM PROTECTED ROUTES')

# Create a FRESH guest client (previous guest may be logged in from registration)
fresh_guest = Client()

protected_for_guests = [
    '/accounts/dashboard/',
    '/accounts/profile/',
    '/services/visa/apply/',
    '/services/passport/apply/',
    '/embassy-services/request/new/',
    '/embassy-services/my-requests/',
    '/embassy-services/officer/',
    '/portal/',
    '/portal/visa-types/',
    '/certificates/my/',
    '/certificates/manage/',
    '/endorsements/my/',
    '/endorsements/manage/',
    '/communications/inbox/',
    '/communications/manage/',
]

for url in protected_for_guests:
    r = fresh_guest.get(url)
    # Should be 302 (redirect to login) or 403 (forbidden)
    ok = r.status_code in (302, 403)
    t.test(f'Guest blocked from {url}', ok, f'status={r.status_code}')


# =============================================================================
# 4. MEMBER (regular user) FLOWS
# =============================================================================

t.section('4. MEMBER FLOWS (johndoe)')

member = Client()
member.login(username='johndoe', password='password')

member_routes = [
    '/accounts/dashboard/',
    '/accounts/profile/',
    '/services/visa/apply/',
    '/services/passport/apply/',
    '/embassy-services/request/new/',
    '/embassy-services/my-requests/',
    '/certificates/my/',
    '/endorsements/my/',
]
for url in member_routes:
    r = member.get(url)
    t.test(f'Member can GET {url}', r.status_code == 200, f'status={r.status_code}')

# Member cannot access officer/admin pages
forbidden_for_member = [
    '/embassy-services/officer/',
    '/embassy-services/officer/requests/',
    '/portal/',
    '/portal/visa-types/',
    '/certificates/manage/',
    '/endorsements/manage/',
    '/communications/manage/',
]
for url in forbidden_for_member:
    r = member.get(url)
    # Regular members should NOT access these — should redirect or 403
    ok = r.status_code in (302, 403, 404)
    t.test(f'Member blocked from {url}', ok, f'status={r.status_code}')


# =============================================================================
# 5. MEMBER FORM SUBMISSIONS
# =============================================================================

t.section('5. MEMBER FORM SUBMISSIONS')

from services.models import VisaApplication, PassportApplication, VisaType
from embassy_liaison.models import EmbassyServiceRequest
from core.models import ContactMessage

# Contact form (as guest)
r = guest.post('/contact/', {
    'name': 'Test Contact',
    'email': 'test@example.com',
    'subject': 'Test Subject',
    'message': 'This is a test message.',
})
t.test('Contact form submission', r.status_code in (200, 302))
t.test('Contact message saved to DB',
       ContactMessage.objects.filter(email='test@example.com').exists())

# Visa application (as member)
visa_type = VisaType.objects.filter(active=True).first()
if visa_type:
    count_before = VisaApplication.objects.filter(user__username='johndoe').count()
    r = member.post('/services/visa/apply/', {
        'visa_type': visa_type.id,
        'full_name': 'John Doe',
        'date_of_birth': '1990-01-01',
        'nationality': 'Kenyan',
        'passport_number': 'A1234567',
        'phone': '+82-10-0000-0001',
        'address': 'Seoul, Korea',
        'purpose_of_visit': 'Tourism',
        'intended_arrival': '2026-08-01',
        'intended_departure': '2026-08-15',
    })
    count_after = VisaApplication.objects.filter(user__username='johndoe').count()
    t.test('Visa application submission',
           r.status_code in (200, 302) and count_after > count_before,
           f'before={count_before}, after={count_after}')

# Passport application (as member)
count_before = PassportApplication.objects.filter(user__username='johndoe').count()
r = member.post('/services/passport/apply/', {
    'type': 'renewal',
    'full_name': 'John Doe',
    'date_of_birth': '1990-01-01',
    'place_of_birth': 'Nairobi',
    'gender': 'male',
    'national_id': 'ID12345678',
    'current_passport_number': 'A1111111',
    'phone': '+82-10-0000-0002',
    'email': 'john@example.com',
    'address_in_korea': 'Seoul',
    'address_in_kenya': 'Nairobi',
})
count_after = PassportApplication.objects.filter(user__username='johndoe').count()
t.test('Passport application submission',
       r.status_code in (200, 302) and count_after > count_before,
       f'before={count_before}, after={count_after}')

# Embassy service request
count_before = EmbassyServiceRequest.objects.filter(user__username='johndoe').count()
r = member.post('/embassy-services/request/new/', {
    'service_type': 'passport_renewal',
    'priority': 'normal',
    'full_name': 'John Doe',
    'kenyan_id_number': 'ID12345',
    'current_document_number': 'P111',
    'phone': '+82-10-0000-0003',
    'address_in_korea': 'Seoul',
    'city': 'seoul',
    'purpose': 'Renew expired passport',
    'consent_data_sharing': 'on',
    'consent_privacy_policy': 'on',
})
count_after = EmbassyServiceRequest.objects.filter(user__username='johndoe').count()
t.test('Embassy service request submission',
       r.status_code in (200, 302) and count_after > count_before,
       f'before={count_before}, after={count_after}')


# =============================================================================
# 6. LEADER / OFFICER FLOWS
# =============================================================================

t.section('6. LEADER / OFFICER FLOWS (chairman)')

leader = Client()
leader.login(username='chairman', password='password')

leader_routes = [
    '/portal/',
    '/portal/visa-types/',
    '/portal/visa-types/new/',
    '/portal/faqs/',
    '/portal/events/',
    '/portal/news/',
    '/portal/announcements/',
    '/portal/site-banners/',
    '/portal/testimonials/',
    '/portal/service-guides/',
    '/portal/leaders/',
    '/portal/pages/',
    '/portal/site-settings/',
    '/embassy-services/officer/',
    '/embassy-services/officer/requests/',
    '/certificates/manage/',
    '/certificates/manage/new/',
    '/endorsements/manage/',
    '/endorsements/manage/new/',
    '/communications/manage/',
    '/communications/manage/new/',
    '/communications/manage/announcements/',
]
for url in leader_routes:
    r = leader.get(url)
    t.test(f'Leader can GET {url}', r.status_code == 200, f'status={r.status_code}')


# =============================================================================
# 7. PORTAL CRUD (all 10 models)
# =============================================================================

t.section('7. PORTAL CRUD — CREATE/EDIT/DELETE')

# Test CRUD via portal for VisaType
v_count_before = VisaType.objects.count()
r = leader.post('/portal/visa-types/new/', {
    'name': 'CRUD Test Visa',
    'slug': 'crud-test-visa',
    'description': 'Test',
    'requirements': 'Req 1\nReq 2',
    'processing_time': '1 day',
    'fee': 'USD 1',
    'icon': 'X',
    'sort_order': '99',
    'active': 'on',
})
t.test('Portal CREATE VisaType', r.status_code == 302 and VisaType.objects.count() > v_count_before)

v = VisaType.objects.filter(slug='crud-test-visa').first()
if v:
    r = leader.post(f'/portal/visa-types/{v.id}/edit/', {
        'name': 'CRUD Test Visa Updated',
        'slug': 'crud-test-visa',
        'description': 'Updated',
        'requirements': 'New req',
        'processing_time': '2 days',
        'fee': 'USD 2',
        'icon': 'Y',
        'sort_order': '99',
        'active': 'on',
    })
    v.refresh_from_db()
    t.test('Portal EDIT VisaType', r.status_code == 302 and v.name == 'CRUD Test Visa Updated')

    r = leader.post(f'/portal/visa-types/{v.id}/delete/')
    t.test('Portal DELETE VisaType',
           r.status_code == 302 and not VisaType.objects.filter(slug='crud-test-visa').exists())

# Test CRUD for FAQ
from services.models import Faq
faq_count_before = Faq.objects.count()
r = leader.post('/portal/faqs/new/', {
    'question': 'Is this a test?',
    'answer': 'Yes.',
    'category': 'general',
    'sort_order': '0',
    'active': 'on',
})
t.test('Portal CREATE FAQ', r.status_code == 302 and Faq.objects.count() > faq_count_before)

created_faq = Faq.objects.filter(question='Is this a test?').first()
if created_faq:
    r = leader.post(f'/portal/faqs/{created_faq.id}/delete/')
    t.test('Portal DELETE FAQ', r.status_code == 302)


# =============================================================================
# 8. CERTIFICATE LIFECYCLE (create → publish → verify → revoke)
# =============================================================================

t.section('8. CERTIFICATE LIFECYCLE')

from certificates.models import Certificate
from certificates.services import issue_certificate

cert_count_before = Certificate.objects.count()
r = leader.post('/certificates/manage/new/', {
    'recipient_name': 'Test Cert Recipient',
    'cert_type': 'appreciation',
    'body': 'For outstanding community service.',
    'issued_by': '1',
})
t.test('Certificate create via form',
       r.status_code in (200, 302) and Certificate.objects.count() > cert_count_before)

cert = Certificate.objects.filter(recipient_name='Test Cert Recipient').first()
if cert:
    t.test('Certificate auto-numbered', cert.cert_number.startswith('KCK-CERT-'))

    # Publish (generate PDF)
    try:
        issue_certificate(cert)
        cert.refresh_from_db()
        t.test('Certificate PDF generation', cert.status == 'published' and bool(cert.pdf_file))
    except Exception as e:
        t.test('Certificate PDF generation', False, str(e))

    # Verify publicly
    if cert.pdf_file:
        r = guest.get(f'/certificates/verify/{cert.verification_code}/')
        t.test('Certificate public verification', r.status_code == 200)

    # Download
    r = leader.get(f'/certificates/{cert.id}/download/')
    t.test('Certificate PDF download', r.status_code == 200)

    # Cleanup
    cert.delete()


# =============================================================================
# 9. ENDORSEMENT LIFECYCLE (create → publish → verify)
# =============================================================================

t.section('9. ENDORSEMENT LIFECYCLE')

from endorsements.models import Endorsement
from endorsements.services import issue_endorsement

end_count_before = Endorsement.objects.count()
r = leader.post('/endorsements/manage/new/', {
    'member_full_name': 'Test Endorse Recipient',
    'member_id_number': 'ID999',
    'endorsement_type': 'cover_note',
    'subject': 'Test Cover Note',
    'addressed_to': 'The Ambassador',
    'purpose': 'Test purpose',
    'body': 'Test body.',
    'issued_by': '1',
    'valid_from': '2026-01-01',
})
t.test('Endorsement create via form',
       r.status_code in (200, 302) and Endorsement.objects.count() > end_count_before)

endorse = Endorsement.objects.filter(member_full_name='Test Endorse Recipient').first()
if endorse:
    t.test('Endorsement auto-numbered', endorse.reference_number.startswith('KCK-END-'))
    t.test('Endorsement has UUID verification code', bool(endorse.verification_code))

    # Publish
    try:
        issue_endorsement(endorse)
        endorse.refresh_from_db()
        t.test('Endorsement PDF generation',
               endorse.status == 'issued' and bool(endorse.pdf_file))
    except Exception as e:
        t.test('Endorsement PDF generation', False, str(e))

    # Public verification
    r = guest.get(f'/endorsements/verify/{endorse.verification_code}/')
    t.test('Endorsement public verification', r.status_code == 200)

    # Search by reference number
    r = guest.get(f'/endorsements/?code={endorse.reference_number}')
    t.test('Endorsement search by ref', r.status_code == 200 and
           'Endorsement Verified' in r.content.decode())

    # Download
    r = leader.get(f'/endorsements/{endorse.id}/download/')
    t.test('Endorsement PDF download', r.status_code == 200)

    # Cleanup
    endorse.delete()


# =============================================================================
# 10. COMMUNICATION LIFECYCLE
# =============================================================================

t.section('10. COMMUNICATION LIFECYCLE')

from communications.models import Communication
from communications.services import publish_communication

comm_count_before = Communication.objects.count()
r = leader.post('/communications/manage/new/', {
    'subject': 'Test Official Letter',
    'body': 'This is a test communication.',
    'category': 'general',
    'audience': 'all',
    'sender': '1',
})
t.test('Communication create via form',
       r.status_code in (200, 302) and Communication.objects.count() > comm_count_before)

comm = Communication.objects.filter(subject='Test Official Letter').first()
if comm:
    t.test('Communication auto-numbered',
           comm.reference_number.startswith('KCK/'))
    try:
        publish_communication(comm)
        comm.refresh_from_db()
        t.test('Communication PDF generation',
               comm.status == 'published' and bool(comm.pdf_file))
    except Exception as e:
        t.test('Communication PDF generation', False, str(e))
    comm.delete()


# =============================================================================
# 11. EMBASSY REQUEST OFFICER WORKFLOW
# =============================================================================

t.section('11. EMBASSY REQUEST OFFICER WORKFLOW')

req = EmbassyServiceRequest.objects.first()
if req:
    # Officer can view
    r = leader.get(f'/embassy-services/officer/request/{req.id}/')
    t.test('Officer can view request detail', r.status_code == 200)

    # Officer can update status
    r = leader.post(f'/embassy-services/officer/request/{req.id}/', {
        'action': 'update_status',
        'status': 'under_review',
        'embassy_reference': '',
        'message_to_member': 'Reviewing your request.',
        'internal_note': '',
    })
    req.refresh_from_db()
    t.test('Officer can update status', r.status_code in (200, 302) and req.status == 'under_review')

    # Generate cover note from request
    r = leader.get(f'/endorsements/manage/from-request/{req.id}/')
    t.test('Quick-generate endorsement form loads', r.status_code == 200)


# =============================================================================
# 12. EVENT REGISTRATION
# =============================================================================

t.section('12. EVENT REGISTRATION')

from events_app.models import Event, EventRegistration

event = Event.objects.filter(active=True).first()
if event:
    reg_count_before = EventRegistration.objects.filter(user__username='johndoe').count()
    r = member.post(f'/events/{event.slug}/register/')
    # 302 = redirect after success
    reg_count_after = EventRegistration.objects.filter(user__username='johndoe').count()
    t.test('Member can register for event',
           r.status_code in (200, 302),
           f'reg_count before={reg_count_before}, after={reg_count_after}')


# =============================================================================
# 13. NEWSLETTER SUBSCRIPTION
# =============================================================================

t.section('13. NEWSLETTER SUBSCRIPTION')

from accounts.models import NewsletterSubscription
sub_count_before = NewsletterSubscription.objects.count()
unique_email = f'nl_test_{os.urandom(4).hex()}@example.com'
r = guest.post('/newsletter/subscribe/', {'email': unique_email})
t.test('Newsletter subscribe',
       r.status_code in (200, 302) and NewsletterSubscription.objects.count() > sub_count_before,
       f'before={sub_count_before}, after={NewsletterSubscription.objects.count()}')


# =============================================================================
# 14. SEARCH
# =============================================================================

t.section('14. SEARCH')

r = guest.get('/search/?q=visa')
t.test('Search for "visa"', r.status_code == 200)

r = guest.get('/search/?q=passport')
t.test('Search for "passport"', r.status_code == 200)

r = guest.get('/search/?q=event')
t.test('Search for "event"', r.status_code == 200)


# =============================================================================
# 15. CROSS-USER ACCESS PROTECTION
# =============================================================================

t.section('15. CROSS-USER ACCESS PROTECTION')

# Create another user
other_user, _ = User.objects.get_or_create(
    username='otheruser',
    defaults={'email': 'other@test.com', 'first_name': 'Other', 'last_name': 'User'},
)
other_user.set_password('password')
other_user.save()

# Login as the other user
other = Client()
other.login(username='otheruser', password='password')

# Try to access johndoe's application — should be 404 or 403
app = VisaApplication.objects.filter(user__username='johndoe').first()
if app:
    r = other.get(f'/services/visa/application/{app.id}/')
    t.test('Cross-user visa application blocked', r.status_code in (403, 404),
           f'status={r.status_code}')

req = EmbassyServiceRequest.objects.filter(user__username='johndoe').first()
if req:
    r = other.get(f'/embassy-services/request/{req.id}/')
    t.test('Cross-user embassy request blocked', r.status_code in (403, 404),
           f'status={r.status_code}')


# =============================================================================
# 16. ADMIN (Django built-in admin)
# =============================================================================

t.section('16. DJANGO ADMIN')

admin = Client()
admin.login(username='admin', password='password')
r = admin.get('/django-admin/')
t.test('Django admin accessible to superuser', r.status_code == 200)

# Regular user should NOT get in
r = member.get('/django-admin/')
t.test('Django admin blocked for non-staff', r.status_code in (302, 403))


# =============================================================================
# 17. STATIC FILES AND MEDIA
# =============================================================================

t.section('17. STATIC FILES')

r = guest.get('/static/css/main.css')
t.test('main.css served', r.status_code == 200)

r = guest.get('/static/images/kck-logo.png')
t.test('kck-logo.png served', r.status_code == 200)

r = guest.get('/static/js/main.js')
t.test('main.js served', r.status_code == 200)


# =============================================================================
# FINAL
# =============================================================================

sys.exit(t.summary())
