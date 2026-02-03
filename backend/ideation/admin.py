from django.contrib import admin
from .models import UseCase, FeasibilityAssessment, RefinedPlay


@admin.register(UseCase)
class UseCaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'research_job', 'priority', 'status', 'impact_score', 'feasibility_score']
    list_filter = ['priority', 'status', 'created_at']
    search_fields = ['title', 'description', 'business_problem']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(FeasibilityAssessment)
class FeasibilityAssessmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'use_case', 'overall_feasibility', 'overall_score', 'created_at']
    list_filter = ['overall_feasibility', 'created_at']
    search_fields = ['use_case__title', 'recommendations']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(RefinedPlay)
class RefinedPlayAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'use_case', 'target_persona', 'status', 'created_at']
    list_filter = ['status', 'target_vertical', 'created_at']
    search_fields = ['title', 'elevator_pitch', 'value_proposition']
    readonly_fields = ['id', 'created_at', 'updated_at']
