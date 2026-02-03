"""Serializers for the assets API."""
from rest_framework import serializers
from .models import Persona, OnePager, AccountPlan, Citation


class PersonaSerializer(serializers.ModelSerializer):
    """Serializer for buyer personas."""

    class Meta:
        model = Persona
        fields = [
            'id',
            'research_job',
            'name',
            'title',
            'department',
            'seniority_level',
            'background',
            'goals',
            'challenges',
            'motivations',
            'decision_criteria',
            'preferred_communication',
            'objections',
            'content_preferences',
            'key_messages',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OnePagerSerializer(serializers.ModelSerializer):
    """Serializer for one-pagers."""

    class Meta:
        model = OnePager
        fields = [
            'id',
            'research_job',
            'title',
            'headline',
            'executive_summary',
            'challenge_section',
            'solution_section',
            'benefits_section',
            'differentiators',
            'call_to_action',
            'next_steps',
            'html_content',
            'pdf_path',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'html_content', 'pdf_path', 'created_at', 'updated_at']


class AccountPlanSerializer(serializers.ModelSerializer):
    """Serializer for account plans."""

    class Meta:
        model = AccountPlan
        fields = [
            'id',
            'research_job',
            'title',
            'executive_summary',
            'account_overview',
            'strategic_objectives',
            'key_stakeholders',
            'opportunities',
            'competitive_landscape',
            'swot_analysis',
            'engagement_strategy',
            'value_propositions',
            'action_plan',
            'success_metrics',
            'milestones',
            'timeline',
            'html_content',
            'pdf_path',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'html_content', 'pdf_path', 'created_at', 'updated_at']


class CitationSerializer(serializers.ModelSerializer):
    """Serializer for citations."""

    class Meta:
        model = Citation
        fields = [
            'id',
            'research_job',
            'citation_type',
            'title',
            'source',
            'url',
            'author',
            'publication_date',
            'excerpt',
            'relevance_note',
            'verified',
            'verification_date',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class GenerateAssetSerializer(serializers.Serializer):
    """Serializer for asset generation requests."""

    research_job_id = serializers.UUIDField()
    use_case_id = serializers.UUIDField(required=False, allow_null=True)
