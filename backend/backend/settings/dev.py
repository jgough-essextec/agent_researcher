"""
Django development settings.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Add browsable API in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(  # noqa: F405
    'rest_framework.renderers.BrowsableAPIRenderer'
)
