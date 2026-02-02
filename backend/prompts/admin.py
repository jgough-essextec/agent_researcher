from django.contrib import admin
from .models import PromptTemplate


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'created_at', 'updated_at']
    list_filter = ['is_default']
    search_fields = ['name', 'content']
