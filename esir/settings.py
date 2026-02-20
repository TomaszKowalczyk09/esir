import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Bezpieczne ustawienia z ENV (nie commitujemy sekretów) ---
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    # dev fallback (nie używać na produkcji)
    SECRET_KEY = "dev-only-change-me"

DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

# ALLOWED_HOSTS jako lista rozdzielona przecinkami
ALLOWED_HOSTS = [h.strip() for h in os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,sesja.gminagryfino.pl",
    ".vercel.app",
).split(",") if h.strip()]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'accounts',
    'core',
]

AUTH_USER_MODEL = 'accounts.Uzytkownik'

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'esir.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

LANGUAGE_CODE = "pl"
USE_I18N = True
TIMEZONE = 'Europe/Warsaw'
USE_TZ = True

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/panel/'
LOGOUT_REDIRECT_URL = '/login/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Security hardening (ma sens przy HTTPS / produkcji)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# Włącz wtedy, gdy serwer działa po HTTPS
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "0") == "1"
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "0") == "1"
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "0") == "1"

# HSTS (tylko dla HTTPS)
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", "0") == "1"
SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_SECURE_HSTS_PRELOAD", "0") == "1"

# Cloudflare / reverse proxy
# Jeśli aplikacja stoi za Cloudflare (Flexible/Full) i reverse proxy ustawia X-Forwarded-Proto,
# Django musi to respektować, żeby poprawnie oznaczać request.is_secure() i wystawiać ciasteczka.
BEHIND_CLOUDFLARE = os.environ.get("DJANGO_BEHIND_CLOUDFLARE", "0") == "1"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Włącz wtedy, gdy serwer działa po HTTPS (za CF najlepiej włączyć)
if BEHIND_CLOUDFLARE and os.environ.get("DJANGO_SECURE_SSL_REDIRECT") is None:
    SECURE_SSL_REDIRECT = True

# dodatkowe nagłówki
REFERRER_POLICY = "same-origin"

# --- Static files ---
# URL pod jakim serwowane są statyki
STATIC_URL = "/static/"

# Źródła statyków w repo (ten katalog ma być w Git)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Katalog wyjściowy dla `collectstatic` (nie commitować)
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: serwowanie statyków (w tym admin CSS/JS) bezpośrednio z Django
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# (opcjonalnie) media upload
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
