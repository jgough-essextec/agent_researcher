"""Serializers for the memory/knowledge base API."""
from rest_framework import serializers
from .models import ClientProfile, SalesPlay, MemoryEntry


class ClientProfileSerializer(serializers.ModelSerializer):
    """Serializer for client profiles."""

    class Meta:
        model = ClientProfile
        fields = [
            'id',
            'client_name',
            'industry',
            'company_size',
            'region',
            'key_contacts',
            'summary',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'vector_id', 'created_at', 'updated_at']


class SalesPlaySerializer(serializers.ModelSerializer):
    """Serializer for sales plays."""

    class Meta:
        model = SalesPlay
        fields = [
            'id',
            'title',
            'play_type',
            'content',
            'context',
            'industry',
            'vertical',
            'usage_count',
            'success_rate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'vector_id', 'usage_count', 'created_at', 'updated_at']


class MemoryEntrySerializer(serializers.ModelSerializer):
    """Serializer for memory entries."""

    class Meta:
        model = MemoryEntry
        fields = [
            'id',
            'entry_type',
            'title',
            'content',
            'client_name',
            'industry',
            'tags',
            'source_type',
            'source_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'vector_id', 'created_at', 'updated_at']


class ContextQuerySerializer(serializers.Serializer):
    """Serializer for context query requests."""

    client_name = serializers.CharField(max_length=255)
    industry = serializers.CharField(max_length=100, required=False, allow_blank=True)
    query = serializers.CharField(max_length=500, required=False, allow_blank=True)
