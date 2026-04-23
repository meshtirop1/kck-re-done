"""
Django settings for kck_project - Kenya Community in Korea website
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-this-in-production-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

DEBUG = False

ALLOWED_HOSTS = [
    'kenyakorea.com',
    'www.kenyakorea.com',
    'sports.kenyakorea.com',
    'localhost',
    'sports.localhost',
    '127.0.0.1',
    '*',  # allow all during development; tighten in production
]

# CSRF trusted origins (needed for HTTPS form submissions)
CSRF_TRUSTED_ORIGINS = [
    'https://kenyakorea.com',
    'https://www.kenyakorea.com',
    'https://sports.kenyakorea.com',
]

# Subdomain URLs for templates / links
SPORTS_SUBDOMAIN_URL = 'https://sports.kenyakorea.com'

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

# Email (console for dev)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@kenyakorea.com'

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
