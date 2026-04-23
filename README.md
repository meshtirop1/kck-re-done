# KCK Django Project

Kenya Community in Korea (KCK) - Django implementation of the embassy/community website.

## Stack

- **Backend:** Django 6.x, Python 3.14
- **Frontend:** HTML, Bootstrap 5.3, Bootstrap Icons, Custom CSS, Vanilla JS
- **Database:** SQLite (development)
- **Forms:** django-crispy-forms with crispy-bootstrap5
- **Auth:** Built-in Django auth with custom User model

## Features

### Public
- Homepage with dynamic content (visa types, events, testimonials, news)
- About page with mission/vision
- Visa types catalog and online application
- Passport application system (new/renewal/replacement)
- Events listing, detail pages, and online registration
- News/announcements
- Testimonials
- FAQ system with categories
- Contact form
- Global search across content
- Newsletter subscription
- Ambassador profile page
- Community pages (history, mission, vision, location, hours)

### User
- Registration & login
- Dashboard with applications and event registrations
- Profile editing with photo upload
- Password change
- Application status tracking

### Admin (Django Admin)
- Full CRUD for visa types, events, FAQs, news, testimonials, pages
- Application review with status updates
- Bulk approve/reject actions
- Contact message management
- User management with admin toggle
- Announcement banners
- Site settings (singleton)
- Event gallery uploads

### Extra Features Added
- **Newsletter subscription** system
- **Announcement banner** with time-based activation
- **News articles** with featured images
- **Testimonials** from community members
- **Event gallery** for past events
- **Site-wide search** across visa types, events, news, and FAQs
- **Global site settings** (editable via admin)
- **Ambassador profile** with photo and welcome message
- **Back-to-top button**
- **Auto-dismissing alerts**
- **Bootstrap Icons** throughout for visual polish

## Project Structure

```
kck_brir_django/
├── kck_project/          # Main Django settings
├── accounts/             # User, auth, profile, newsletter
├── core/                 # Homepage, contact, about, search, site settings
├── services/             # Visa types, applications, passport, FAQs
├── events_app/           # Events, registrations, gallery
├── community/            # News, testimonials, pages, announcements
├── templates/            # All Bootstrap 5 templates
├── static/               # Custom CSS/JS
├── media/                # User uploads
└── manage.py
```

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install django pillow django-crispy-forms crispy-bootstrap5

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Seed sample data
python manage.py seed_data

# Create a superuser (optional - seed creates one)
python manage.py createsuperuser

# Run the server
python manage.py runserver
```

## Default Credentials (after seeding)

- **Admin:** admin@kenyakorea.com / password
- **Sample user:** john@example.com / password

## URLs

- `/` — Homepage
- `/about/` — About page
- `/contact/` — Contact form
- `/services/visa/types/` — Visa types
- `/services/visa/apply/` — Visa application (auth required)
- `/services/passport/apply/` — Passport application (auth required)
- `/events/` — Events list
- `/community/news/` — News list
- `/accounts/login/` — Login
- `/accounts/register/` — Register
- `/accounts/dashboard/` — User dashboard (auth required)
- `/django-admin/` — Django admin panel

## Design

Preserves the original KCK branding:
- Primary blue: `#0B3D91`
- Accent red: `#C8102E`
- Gold: `#FFD700`
- Font: Figtree via Google Fonts
