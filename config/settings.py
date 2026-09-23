"""Django settings for the reader-study site.

The site runs in one of three modes, chosen with the NESHAT_MODE environment variable:

- "dev" (default): your own computer. Debug pages on, any host name allowed.
- "venue": the offline laptop at the workshop. Plain HTTP on a private Wi-Fi router.
- "online": the real server in Iran, behind HTTPS.

Study data (the database, case images, the secret key) lives in data/, which git ignores.
"""

import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("NESHAT_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

SITE_MODE = os.environ.get("NESHAT_MODE", "dev")
if SITE_MODE not in {"dev", "venue", "online"}:
    raise RuntimeError(f"NESHAT_MODE must be dev, venue or online, not {SITE_MODE!r}")

DEBUG = SITE_MODE == "dev"

# The product name is not decided yet. Change it here (or with NESHAT_SITE_NAME) when it is.
SITE_NAME = os.environ.get("NESHAT_SITE_NAME", "[Product name]")


def _secret_key() -> str:
    """Read the secret key from the environment, or from data/secret_key.txt (made once)."""
    if key := os.environ.get("NESHAT_SECRET_KEY"):
        return key
    key_file = DATA_DIR / "secret_key.txt"
    if not key_file.exists():
        key_file.write_text(get_random_secret_key(), encoding="utf-8")
    return key_file.read_text(encoding="utf-8").strip()


SECRET_KEY = _secret_key()

if SITE_MODE == "online":
    ALLOWED_HOSTS = [h for h in os.environ.get("NESHAT_HOSTS", "").split(",") if h]
else:
    # dev and venue run on a private network whose address changes (laptop IP, router IP).
    ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "reading",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "reading.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# One SQLite file. WAL mode lets readers and one writer work at the same time.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            "init_command": (
                "PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;PRAGMA busy_timeout=5000"
            ),
            "transaction_mode": "IMMEDIATE",
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("fa", "فارسی")]
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# Style and script files. WhiteNoise serves them in every mode, with no internet needed.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # filled by `manage.py collectstatic` for venue/online
STATIC_ROOT.mkdir(exist_ok=True)
WHITENOISE_USE_FINDERS = DEBUG

# Case images are NOT public files. They are served only through views that check access.
CASE_MEDIA_ROOT = DATA_DIR / "media"

# Message colours match the notice styles in reading-room.css.
MESSAGE_TAGS = {10: "info", 20: "info", 25: "ok", 30: "warn", 40: "stop"}

# Security headers. Everything the page loads must come from this site (offline-first rule).
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:", "blob:"],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF],
    "font-src": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.NONE],
    "frame-ancestors": [CSP.NONE],
    "form-action": [CSP.SELF],
}
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

if SITE_MODE == "online":
    # The online server sits behind HTTPS. Browsers then send cookies only over HTTPS.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS]
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
