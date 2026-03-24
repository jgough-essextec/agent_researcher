"""
Django production settings.
"""
import os
import dj_database_url
from .base import *  # noqa: F401, F403

DEBUG = False

# Secret key — must be set explicitly in production
_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    raise RuntimeError('SECRET_KEY environment variable must be set in production')
SECRET_KEY = _secret_key

# Hosts — must be set explicitly in production
_allowed_hosts = os.environ.get('ALLOWED_HOSTS', '')
if not _allowed_hosts:
    raise RuntimeError('ALLOWED_HOSTS environment variable must be set in production')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()]

# Database - PostgreSQL via DATABASE_URL
_database_url = os.environ.get('DATABASE_URL')
if not _database_url:
    raise RuntimeError('DATABASE_URL environment variable must be set in production')
DATABASES = {
    'default': dj_database_url.config(
        default=_database_url,
        conn_max_age=600,
    )
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Whitenoise middleware (insert after SecurityMiddleware)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Security settings — SSL redirect on by default in production; set SECURE_SSL_REDIRECT=false to disable (e.g. behind a load balancer that terminates SSL)
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS — must be set explicitly in production; never allow all origins
_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if not _cors_origins:
    raise RuntimeError('CORS_ALLOWED_ORIGINS environment variable must be set in production')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(',') if o.strip()]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
