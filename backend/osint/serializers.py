from rest_framework import serializers
from .models import (
    OsintJob,
    DnsFinding,
    SubdomainFinding,
    InfrastructureFinding,
    EmailSecurityAssessment,
    ScreenshotUpload,
    ServiceMapping,
)

# Status values that indicate a phase is completed.
_PHASE1_COMPLETE_STATUSES = {
    'phase1_complete',
    'phase2_auto',
    'awaiting_terminal_output',
    'phase2_processing',
    'awaiting_screenshots',
    'phase3_processing',
    'phase4_analysis',
    'phase5_report',
    'completed',
}
_PHASE2_AUTO_COMPLETE_STATUSES = {
    'awaiting_terminal_output',
    'phase2_processing',
    'awaiting_screenshots',
    'phase3_processing',
    'phase4_analysis',
    'phase5_report',
    'completed',
}
_PHASE2_MANUAL_COMPLETE_STATUSES = {
    'awaiting_screenshots',
    'phase3_processing',
    'phase4_analysis',
    'phase5_report',
    'completed',
}
_PHASE3_COMPLETE_STATUSES = {
    'phase4_analysis',
    'phase5_report',
    'completed',
}
_PHASE4_COMPLETE_STATUSES = {
    'phase5_report',
    'completed',
}


class OsintJobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OsintJob
        fields = [
            'organization_name',
            'primary_domain',
            'additional_domains',
            'engagement_context',
            'research_job',
        ]


class OsintJobSerializer(serializers.ModelSerializer):
    findings_summary = serializers.SerializerMethodField()
    phase_progress = serializers.SerializerMethodField()

    class Meta:
        model = OsintJob
        fields = '__all__'
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def get_findings_summary(self, obj: OsintJob) -> dict:
        return {
            'subdomains_found': obj.subdomain_findings.count(),
            'dns_records': obj.dns_findings.count(),
            'email_assessments': obj.email_assessments.count(),
            'screenshots': obj.screenshots.count(),
        }

    def get_phase_progress(self, obj: OsintJob) -> dict:
        status = obj.status
        return {
            'phase1': 'completed' if status in _PHASE1_COMPLETE_STATUSES else 'pending',
            'phase2_auto': 'completed' if status in _PHASE2_AUTO_COMPLETE_STATUSES else 'pending',
            'phase2_manual': 'completed' if status in _PHASE2_MANUAL_COMPLETE_STATUSES else 'pending',
            'phase3': 'completed' if status in _PHASE3_COMPLETE_STATUSES else 'pending',
            'phase4': 'completed' if status in _PHASE4_COMPLETE_STATUSES else 'pending',
            'phase5': 'completed' if status == 'completed' else 'pending',
        }


class DnsFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DnsFinding
        fields = '__all__'


class SubdomainFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubdomainFinding
        fields = '__all__'


class InfrastructureFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureFinding
        fields = '__all__'


class EmailSecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSecurityAssessment
        fields = '__all__'


class ScreenshotUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreenshotUpload
        fields = '__all__'


class ServiceMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceMapping
        fields = '__all__'
