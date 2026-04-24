"""
Django settings for kck_project — Kenya Community in Korea.

Environment variables override file defaults so the same codebase can run
in dev, Docker, and production without edits. See .env.example for the
full list and how to set them.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ('1', 'true', 'yes', 'on')


def _env_list(name, default):
    raw = os.environ.get(name)
    if not raw:
        return list(default)
    return [item.strip() for item in raw.split(',') if item.strip()]


# Load .env if python-dotenv is installed (no-op otherwise)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass


SECRET_KEY = os.environ['DJANGO_SECRET_KEY'] if 'DJANGO_SECRET_KEY' in os.environ else (
    # Dev-only fallback used when no .env is present (fresh clone, ephemeral CI).
    # Production MUST set DJANGO_SECRET_KEY via the environment.
    'django-insecure-dev-only-replace-me-in-production-fallback-value'
)

DEBUG = _env_bool('DEBUG', default=True)

ALLOWED_HOSTS = _env_list('DJANGO_ALLOWED_HOSTS', default=[
    'kenyakorea.com',
    'www.kenyakorea.com',
    'sports.kenyakorea.com',
    'localhost',
    'sports.localhost',
    '127.0.0.1',
    '*',
])

CSRF_TRUSTED_ORIGINS = _env_list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[
    'https://kenyakorea.com',
    'https://www.kenyakorea.com',
    'https://sports.kenyakorea.com',
])

# Subdomain URLs for templates / links
SPORTS_SUBDOMAIN_URL = 'https://sports.kenyakorea.com'


# --------------------------------------------------------------------- #
#  Sentry (error tracking) — only active when SENTRY_DSN is set.
#  No-ops gracefully when the package or DSN is missing.
# --------------------------------------------------------------------- #
_SENTRY_DSN = os.environ.get('SENTRY_DSN', '').strip()
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            integrations=[DjangoIntegration()],
            # % of transactions traced for performance monitoring
            traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            # % of errored transactions that attach a profile
            profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.0')),
            environment=os.environ.get('SENTRY_ENVIRONMENT', 'production'),
            release=os.environ.get('SENTRY_RELEASE') or None,
            send_default_pii=False,        # don't leak user emails/IPs by default
            attach_stacktrace=True,
        )
    except ImportError:
        # sentry-sdk not installed — skip silently; errors still go to the logs.
        pass

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party
    'crispy_forms',
    'crispy_bootstrap5',

    # Local apps
    'accounts',
    'core',
    'services',
    'events_app',
    'community',
    'leaders',
    'certificates',
    'communications',
    'embassy_liaison',
    'endorsements',
    'portal',
    'sports',
    'market',
    'memberships',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom: subdomain-based URL routing (sports.* → sports URLs)
    'kck_project.subdomain_middleware.SubdomainURLRoutingMiddleware',
]

ROOT_URLCONF = 'kck_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_context',
                'memberships.context_processors.membership_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'kck_project.wsgi.application'

# Database. Defaults to SQLite; switches to Postgres if POSTGRES_HOST is set.
# In Docker the SQLite file lives under /app/data (bind-mounted volume).
if os.environ.get('POSTGRES_HOST'):
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'HOST':     os.environ['POSTGRES_HOST'],
            'PORT':     os.environ.get('POSTGRES_PORT', '5432'),
            'NAME':     os.environ.get('POSTGRES_DB',       'kck'),
            'USER':     os.environ.get('POSTGRES_USER',     'kck'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    _sqlite_dir = Path(os.environ.get('SQLITE_DIR', BASE_DIR / 'data'))
    _sqlite_dir.mkdir(parents=True, exist_ok=True)
    _sqlite_file = _sqlite_dir / 'db.sqlite3'
    # One-time migration: if the classic db.sqlite3 exists at the project root
    # and the new data/db.sqlite3 doesn't, prefer the legacy path so we don't
    # silently start with an empty database.
    _legacy = BASE_DIR / 'db.sqlite3'
    if _legacy.exists() and not _sqlite_file.exists():
        _sqlite_file = _legacy
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':   _sqlite_file,
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise — serve compressed & cached static files in production
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
WHITENOISE_AUTOREFRESH = True  # Pick up new files without collectstatic during dev

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom CSRF failure page (matches brand)
CSRF_FAILURE_VIEW = 'core.views.custom_csrf_failure'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# --------------------------------------------------------------------- #
#  Email — read entirely from environment variables.
#  No credentials are hardcoded in this file.
#  Set EMAIL_HOST_USER / EMAIL_HOST_PASSWORD in .env (dev) or the
#  deployment environment (prod). If unset, emails fall back to the
#  console backend so dev never crashes on a missing mailer.
# --------------------------------------------------------------------- #
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = _env_bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = _env_bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
# App passwords are 16 chars; Gmail lets you paste them with or without spaces.
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '').replace(' ', '')
EMAIL_TIMEOUT = 20  # seconds

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    # Credentials missing → print emails to the console instead of crashing.
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    f'Kenya Community in Korea <{EMAIL_HOST_USER or "noreply@kenyakorea.com"}>'
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL  # for admin error emails


# ------------------------------------------------------------------ #
# Production security — env-driven. All default to OFF so local dev
# never trips on them; flip them on via .env when serving HTTPS.
# ------------------------------------------------------------------ #
SECURE_SSL_REDIRECT     = _env_bool('DJANGO_SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE   = _env_bool('DJANGO_SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE      = _env_bool('DJANGO_CSRF_COOKIE_SECURE', default=False)
SECURE_HSTS_SECONDS     = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
SECURE_HSTS_PRELOAD     = _env_bool('DJANGO_SECURE_HSTS_PRELOAD', default=False)
# When behind a reverse proxy that terminates TLS, set this so Django knows
# the request is actually HTTPS.
if _env_bool('DJANGO_BEHIND_PROXY', default=False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Site info
SITE_NAME = 'Kenya Community in Korea'
SITE_SHORT_NAME = 'KCK'
SITE_EMAIL = 'info@kenyakorea.com'
SITE_PHONE = '+82-2-XXXX-XXXX'
SITE_ADDRESS = 'Seoul, South Korea'

# Bootstrap message styling
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
