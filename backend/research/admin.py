from django.contrib import admin
from .models import ResearchJob


@admin.register(ResearchJob)
class ResearchJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'client_name', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['client_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
