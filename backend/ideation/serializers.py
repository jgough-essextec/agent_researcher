"""Serializers for the ideation API."""
from rest_framework import serializers
from .models import UseCase, FeasibilityAssessment, RefinedPlay


class FeasibilityAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for feasibility assessments."""

    class Meta:
        model = FeasibilityAssessment
        fields = [
            'id',
            'overall_feasibility',
            'overall_score',
            'technical_complexity',
            'data_availability',
            'integration_complexity',
            'scalability_considerations',
            'technical_risks',
            'mitigation_strategies',
            'prerequisites',
            'dependencies',
            'recommendations',
            'next_steps',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class RefinedPlaySerializer(serializers.ModelSerializer):
    """Serializer for refined plays."""

    class Meta:
        model = RefinedPlay
        fields = [
            'id',
            'title',
            'elevator_pitch',
            'value_proposition',
            'key_differentiators',
            'target_persona',
            'target_vertical',
            'company_size_fit',
            'discovery_questions',
            'objection_handlers',
            'proof_points',
            'competitive_positioning',
            'next_steps',
            'success_metrics',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UseCaseSerializer(serializers.ModelSerializer):
    """Serializer for use cases."""

    feasibility_assessment = FeasibilityAssessmentSerializer(read_only=True)
    refined_play = RefinedPlaySerializer(read_only=True)

    class Meta:
        model = UseCase
        fields = [
            'id',
            'research_job',
            'title',
            'description',
            'business_problem',
            'proposed_solution',
            'expected_benefits',
            'estimated_roi',
            'time_to_value',
            'technologies',
            'data_requirements',
            'integration_points',
            'priority',
            'impact_score',
            'feasibility_score',
            'status',
            'feasibility_assessment',
            'refined_play',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UseCaseCreateSerializer(serializers.Serializer):
    """Serializer for generating use cases from research."""

    research_job_id = serializers.UUIDField()
