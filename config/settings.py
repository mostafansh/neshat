"""Django settings for the reader-study site.

The site runs in one of three modes, chosen with the NESHAT_MODE environment variable:

- "dev" (default): your own computer only. Debug pages on, reachable only from this computer.
- "venue": the workshop laptop, and phone tests. Plain HTTP on a private Wi-Fi router.
- "online": the real server in Iran, behind HTTPS.

Study data (the database, case images, the secret key, the error log) lives in data/, which
git ignores. How to start each mode: docs/runbook.md.
"""

import os
import sys
from pathlib import Path

from django.contrib.messages import constants as message_level
from django.core.management.utils import get_random_secret_key
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("NESHAT_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)  # 0o700: only our user (on Linux)

SITE_MODE = os.environ.get("NESHAT_MODE", "dev")
if SITE_MODE not in {"dev", "venue", "online"}:
    raise RuntimeError(f"NESHAT_MODE must be dev, venue or online, not {SITE_MODE!r}")

DEBUG = SITE_MODE == "dev"

# The product name (owner's decision, 2026-09-26). NESHAT_SITE_NAME can override it.
SITE_NAME = os.environ.get("NESHAT_SITE_NAME", "AutoClave")


def _secret_key() -> str:
    """Read the secret key from the environment, or from data/secret_key.txt (made once)."""
    if key := os.environ.get("NESHAT_SECRET_KEY"):
        return key
    key_file = DATA_DIR / "secret_key.txt"
    if not key_file.exists():
        key_file.write_text(get_random_secret_key(), encoding="utf-8")
    return key_file.read_text(encoding="utf-8").strip()


SECRET_KEY = _secret_key()

if SITE_MODE == "dev":
    # Empty list + debug on = Django answers only localhost, so debug pages never reach
    # another device. To test on a phone, use venue mode.
    ALLOWED_HOSTS = []
elif SITE_MODE == "venue":
    # The laptop's address on the workshop router is not known in advance.
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = [h.strip() for h in os.environ.get("NESHAT_HOSTS", "").split(",") if h.strip()]
    if not ALLOWED_HOSTS:
        raise RuntimeError("Online mode needs NESHAT_HOSTS, for example NESHAT_HOSTS=study.example.ir")

AUTH_USER_MODEL = "reading.User"
LOGIN_URL = "signin"
LOGIN_REDIRECT_URL = "projects"
LOGOUT_REDIRECT_URL = "home"
CSRF_FAILURE_VIEW = "reading.api.csrf_failure"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",  # the dev server serves files the same way venue does
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
if SITE_MODE == "venue":
    # On the workshop Wi-Fi (plain HTTP) admin pages answer only the laptop itself.
    MIDDLEWARE.append("reading.middleware.admin_only_from_this_computer")

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

# One SQLite file. WAL lets pages read while one save writes. synchronous=FULL flushes every
# save to disk, so a stored first read survives a power cut. busy_timeout (ms) and IMMEDIATE
# make two phones saving at the same moment wait their turn instead of failing.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL;PRAGMA synchronous=FULL;PRAGMA busy_timeout=5000",
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

# Style and script files, served by WhiteNoise straight from static/ in every mode.
# No collectstatic step is needed, and no internet.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)  # an empty folder keeps WhiteNoise from warning at start
WHITENOISE_USE_FINDERS = True

# Case images are NOT public files. They are served only through views that check access.
CASE_MEDIA_ROOT = DATA_DIR / "media"

# Message colours match the notice styles in reading-room.css.
MESSAGE_TAGS = {
    message_level.DEBUG: "info",
    message_level.INFO: "info",
    message_level.SUCCESS: "ok",
    message_level.WARNING: "warn",
    message_level.ERROR: "stop",
}

# Server errors (5xx) and refused requests (4xx, including "This page expired") are written
# to data/errors.log in every mode. Django logs refusals as warnings, so the file takes those.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"timed": {"format": "%(asctime)s %(levelname)s %(message)s"}},
    "handlers": {
        "errors_file": {
            "class": "logging.FileHandler",
            "filename": DATA_DIR / "errors.log",
            "level": "WARNING",
            "formatter": "timed",
            "encoding": "utf-8",
            "delay": True,
        },
    },
    "loggers": {
        "django.request": {"handlers": ["errors_file"]},
        "django.security": {"handlers": ["errors_file"]},
    },
}
if sys.argv[1:2] == ["test"]:
    # The tests make refused requests on purpose. Keep them out of the real log.
    LOGGING["loggers"] = {}

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
if SITE_MODE == "venue":
    # Browsers ignore this header on plain HTTP and log a console error on every page.
    SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

if SITE_MODE == "online":
    # The online server sits behind an HTTPS proxy (nginx or the host's panel). Waitress drops
    # the proxy's X-Forwarded-Proto header unless told to trust it, which causes an endless
    # redirect loop. Start it exactly as in docs/runbook.md:
    #   waitress-serve --listen=127.0.0.1:8000 --trusted-proxy=127.0.0.1
    #     --trusted-proxy-headers="x-forwarded-proto x-forwarded-for" config.wsgi:application
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS]
    # Start short. Raise it only after one HTTPS certificate renewal has worked on the server.
    SECURE_HSTS_SECONDS = int(os.environ.get("NESHAT_HSTS_SECONDS", 60 * 60))
