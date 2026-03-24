"""Tests for the prompts app."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from prompts.models import PromptTemplate


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestPromptTemplate:
    def test_get_default_creates_if_missing(self):
        PromptTemplate.objects.all().delete()
        prompt = PromptTemplate.get_default()
        assert prompt is not None
        assert prompt.is_default is True
        assert prompt.name == 'default'

    def test_get_default_returns_existing(self):
        PromptTemplate.objects.all().delete()
        existing = PromptTemplate.objects.create(
            name='default', content='custom content', is_default=True
        )
        result = PromptTemplate.get_default()
        assert result.pk == existing.pk
        assert result.content == 'custom content'

    def test_only_one_default_exists(self):
        PromptTemplate.objects.all().delete()
        p1 = PromptTemplate.objects.create(name='p1', content='a', is_default=True)
        p2 = PromptTemplate.objects.create(name='p2', content='b', is_default=True)
        p1.refresh_from_db()
        assert p1.is_default is False
        assert p2.is_default is True

    def test_str_representation(self):
        prompt = PromptTemplate(name='my-prompt', content='x', is_default=False)
        assert 'my-prompt' in str(prompt)

    def test_default_content_is_non_empty(self):
        content = PromptTemplate.get_default_content()
        assert isinstance(content, str)
        assert len(content) > 50


@pytest.mark.django_db
class TestDefaultPromptView:
    def test_get_returns_200(self, api_client):
        PromptTemplate.objects.all().delete()
        response = api_client.get('/api/prompts/default/')
        assert response.status_code == 200

    def test_get_returns_default_prompt(self, api_client):
        PromptTemplate.objects.all().delete()
        response = api_client.get('/api/prompts/default/')
        data = response.json()
        assert 'content' in data
        assert data['is_default'] is True

    def test_patch_updates_content(self, api_client):
        PromptTemplate.objects.all().delete()
        response = api_client.patch('/api/prompts/default/', {'content': 'new content'}, format='json')
        assert response.status_code == 200
        assert response.json()['content'] == 'new content'

    def test_put_updates_prompt(self, api_client):
        PromptTemplate.objects.all().delete()
        # First get to create default
        api_client.get('/api/prompts/default/')
        prompt = PromptTemplate.get_default()
        response = api_client.put(
            '/api/prompts/default/',
            {'name': prompt.name, 'content': 'updated', 'is_default': True},
            format='json',
        )
        assert response.status_code == 200
        assert response.json()['content'] == 'updated'
