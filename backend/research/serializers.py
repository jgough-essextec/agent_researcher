from rest_framework import serializers
from .models import ResearchJob, ResearchReport, CompetitorCaseStudy, GapAnalysis, InternalOpsIntel


class ResearchJobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new research job."""

    # Bound unbounded text fields to prevent prompt injection via excessive input
    sales_history = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    prompt = serializers.CharField(max_length=10000, required=False, allow_blank=True)

    class Meta:
        model = ResearchJob
        fields = ['id', 'client_name', 'sales_history', 'prompt']
        read_only_fields = ['id']


class ResearchReportSerializer(serializers.ModelSerializer):
    """Serializer for structured research report (AGE-10)."""

    class Meta:
        model = ResearchReport
        fields = [
            'id',
            'company_overview',
            'founded_year',
            'headquarters',
            'employee_count',
            'annual_revenue',
            'website',
            'recent_news',
            'decision_makers',
            'pain_points',
            'opportunities',
            'digital_maturity',
            'ai_footprint',
            'ai_adoption_stage',
            'strategic_goals',
            'key_initiatives',
            'talking_points',
            'cloud_footprint',
            'security_posture',
            'data_maturity',
            'financial_signals',
            'tech_partnerships',
            'web_sources',
            'synthesis_text',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class CompetitorCaseStudySerializer(serializers.ModelSerializer):
    """Serializer for competitor case studies (AGE-12)."""

    class Meta:
        model = CompetitorCaseStudy
        fields = [
            'id',
            'competitor_name',
            'vertical',
            'case_study_title',
            'summary',
            'technologies_used',
            'outcomes',
            'source_url',
            'relevance_score',
            'created_at',
        ]
        read_only_fields = fields


class GapAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for gap analysis (AGE-13)."""

    class Meta:
        model = GapAnalysis
        fields = [
            'id',
            'technology_gaps',
            'capability_gaps',
            'process_gaps',
            'recommendations',
            'priority_areas',
            'confidence_score',
            'analysis_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


_EMPLOYEE_SENTIMENT_DEFAULTS: dict = {
    'overall_rating': 0.0, 'work_life_balance': 0.0, 'compensation': 0.0,
    'culture': 0.0, 'management': 0.0, 'recommend_pct': 0,
    'positive_themes': [], 'negative_themes': [], 'trend': 'stable',
}
_LINKEDIN_PRESENCE_DEFAULTS: dict = {
    'follower_count': 0, 'engagement_level': 'medium',
    'recent_posts': [], 'employee_trend': 'stable', 'notable_changes': [],
}
_JOB_POSTINGS_DEFAULTS: dict = {
    'total_openings': 0, 'departments_hiring': {}, 'skills_sought': [],
    'seniority_distribution': {}, 'urgency_signals': [], 'insights': '',
}
_NEWS_SENTIMENT_DEFAULTS: dict = {
    'overall_sentiment': 'neutral', 'coverage_volume': 'low',
    'topics': [], 'headlines': [],
}


class InternalOpsIntelSerializer(serializers.ModelSerializer):
    """Serializer for internal operations intelligence (AGE-20)."""

    class Meta:
        model = InternalOpsIntel
        fields = [
            'id',
            'employee_sentiment',
            'linkedin_presence',
            'social_media_mentions',
            'job_postings',
            'news_sentiment',
            'key_insights',
            'gap_correlations',
            'confidence_score',
            'data_freshness',
            'analysis_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)

        def _fill_defaults(field_name: str, defaults: dict) -> None:
            """Merge stored JSON with defaults, replacing any None values."""
            stored = data.get(field_name) or {}
            merged = {**defaults, **{k: v for k, v in stored.items() if v is not None}}
            data[field_name] = merged

        _fill_defaults('employee_sentiment', _EMPLOYEE_SENTIMENT_DEFAULTS)
        _fill_defaults('linkedin_presence', _LINKEDIN_PRESENCE_DEFAULTS)
        _fill_defaults('job_postings', _JOB_POSTINGS_DEFAULTS)
        _fill_defaults('news_sentiment', _NEWS_SENTIMENT_DEFAULTS)

        # Lists at the top level
        if not isinstance(data.get('social_media_mentions'), list):
            data['social_media_mentions'] = []
        if not isinstance(data.get('key_insights'), list):
            data['key_insights'] = []
        if not isinstance(data.get('gap_correlations'), list):
            data['gap_correlations'] = []

        return data


class ResearchJobDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving research job details."""

    report = ResearchReportSerializer(read_only=True)
    competitor_case_studies = CompetitorCaseStudySerializer(many=True, read_only=True)
    gap_analysis = GapAnalysisSerializer(read_only=True)
    internal_ops = InternalOpsIntelSerializer(read_only=True)

    class Meta:
        model = ResearchJob
        fields = [
            'id',
            'client_name',
            'sales_history',
            'prompt',
            'status',
            'current_step',
            'result',
            'error',
            'vertical',
            'report',
            'competitor_case_studies',
            'gap_analysis',
            'internal_ops',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'current_step',
            'result',
            'error',
            'vertical',
            'report',
            'competitor_case_studies',
            'gap_analysis',
            'internal_ops',
            'created_at',
            'updated_at',
        ]
