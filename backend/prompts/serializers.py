from rest_framework import serializers
from .models import PromptTemplate


class PromptTemplateSerializer(serializers.ModelSerializer):
    """Serializer for prompt templates."""

    class Meta:
        model = PromptTemplate
        fields = ['id', 'name', 'content', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'name', 'is_default', 'created_at', 'updated_at']
