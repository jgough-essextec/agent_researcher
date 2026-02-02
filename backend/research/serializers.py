from rest_framework import serializers
from .models import ResearchJob


class ResearchJobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new research job."""

    class Meta:
        model = ResearchJob
        fields = ['id', 'client_name', 'sales_history', 'prompt']
        read_only_fields = ['id']


class ResearchJobDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving research job details."""

    class Meta:
        model = ResearchJob
        fields = ['id', 'client_name', 'sales_history', 'prompt', 'status', 'result', 'error', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'result', 'error', 'created_at', 'updated_at']
