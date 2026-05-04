from django.contrib import admin
from .models import (
    OsintJob,
    DnsFinding,
    SubdomainFinding,
    InfrastructureFinding,
    WhoisRecord,
    EmailSecurityAssessment,
    ScreenshotUpload,
    TerminalSubmission,
    OsintCommandRound,
    OsintReportSection,
    ServiceMapping,
)


@admin.register(OsintJob)
class OsintJobAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'primary_domain', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['organization_name', 'primary_domain']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(DnsFinding)
class DnsFindingAdmin(admin.ModelAdmin):
    list_display = ['domain', 'record_type', 'osint_job']
    list_filter = ['record_type']
    search_fields = ['domain', 'record_value']


@admin.register(SubdomainFinding)
class SubdomainFindingAdmin(admin.ModelAdmin):
    list_display = ['subdomain', 'source', 'category', 'is_alive', 'osint_job']
    list_filter = ['category', 'source', 'is_alive']
    search_fields = ['subdomain']


@admin.register(EmailSecurityAssessment)
class EmailSecurityAssessmentAdmin(admin.ModelAdmin):
    list_display = ['domain', 'has_spf', 'has_dmarc', 'overall_grade', 'osint_job']
    list_filter = ['has_spf', 'has_dmarc', 'overall_grade']
    search_fields = ['domain']


admin.site.register(InfrastructureFinding)
admin.site.register(WhoisRecord)
admin.site.register(ScreenshotUpload)
admin.site.register(TerminalSubmission)
admin.site.register(OsintCommandRound)
admin.site.register(OsintReportSection)
admin.site.register(ServiceMapping)
