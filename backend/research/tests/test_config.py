import pytest
from django.conf import settings


class TestConfiguration:
    """Tests for Django configuration."""

    def test_gemini_api_key_setting_exists(self):
        """Test that GEMINI_API_KEY setting exists."""
        assert hasattr(settings, 'GEMINI_API_KEY')

    def test_cors_settings_configured(self):
        """Test that CORS is properly configured."""
        assert hasattr(settings, 'CORS_ALLOWED_ORIGINS')
        assert 'http://localhost:3000' in settings.CORS_ALLOWED_ORIGINS

    def test_rest_framework_settings(self):
        """Test that REST framework is configured."""
        assert hasattr(settings, 'REST_FRAMEWORK')
        assert 'DEFAULT_PERMISSION_CLASSES' in settings.REST_FRAMEWORK

    def test_installed_apps_include_required(self):
        """Test that required apps are installed."""
        assert 'rest_framework' in settings.INSTALLED_APPS
        assert 'corsheaders' in settings.INSTALLED_APPS
        assert 'research' in settings.INSTALLED_APPS
        assert 'prompts' in settings.INSTALLED_APPS
