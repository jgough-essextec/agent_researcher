from django.contrib import admin
from .models import ResearchJob, ResearchReport, CompetitorCaseStudy, GapAnalysis


@admin.register(ResearchJob)
class ResearchJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'client_name', 'status', 'vertical', 'created_at', 'updated_at']
    list_filter = ['status', 'vertical', 'created_at']
    search_fields = ['client_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ResearchReport)
class ResearchReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'research_job', 'digital_maturity', 'ai_adoption_stage', 'created_at']
    list_filter = ['digital_maturity', 'ai_adoption_stage', 'created_at']
    search_fields = ['research_job__client_name', 'company_overview']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CompetitorCaseStudy)
class CompetitorCaseStudyAdmin(admin.ModelAdmin):
    list_display = ['id', 'competitor_name', 'vertical', 'case_study_title', 'relevance_score', 'created_at']
    list_filter = ['vertical', 'created_at']
    search_fields = ['competitor_name', 'case_study_title', 'summary']
    readonly_fields = ['id', 'created_at']


@admin.register(GapAnalysis)
class GapAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'research_job', 'confidence_score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['research_job__client_name', 'analysis_notes']
    readonly_fields = ['id', 'created_at', 'updated_at']
