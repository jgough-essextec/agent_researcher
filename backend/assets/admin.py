from django.contrib import admin
from .models import Persona, OnePager, AccountPlan, Citation


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'title', 'research_job', 'seniority_level', 'created_at']
    list_filter = ['seniority_level', 'created_at']
    search_fields = ['name', 'title', 'background']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(OnePager)
class OnePagerAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'research_job', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'headline', 'executive_summary']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(AccountPlan)
class AccountPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'research_job', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'executive_summary']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'citation_type', 'source', 'research_job', 'verified', 'created_at']
    list_filter = ['citation_type', 'verified', 'created_at']
    search_fields = ['title', 'source', 'excerpt']
    readonly_fields = ['id', 'created_at']
