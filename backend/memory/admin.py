from django.contrib import admin
from .models import ClientProfile, SalesPlay, MemoryEntry


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'client_name', 'industry', 'company_size', 'created_at']
    list_filter = ['industry', 'created_at']
    search_fields = ['client_name', 'summary']
    readonly_fields = ['id', 'vector_id', 'created_at', 'updated_at']


@admin.register(SalesPlay)
class SalesPlayAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'play_type', 'industry', 'usage_count', 'success_rate']
    list_filter = ['play_type', 'industry', 'created_at']
    search_fields = ['title', 'content', 'context']
    readonly_fields = ['id', 'vector_id', 'created_at', 'updated_at']


@admin.register(MemoryEntry)
class MemoryEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'entry_type', 'title', 'client_name', 'industry', 'created_at']
    list_filter = ['entry_type', 'industry', 'created_at']
    search_fields = ['title', 'content', 'client_name']
    readonly_fields = ['id', 'vector_id', 'created_at', 'updated_at']
