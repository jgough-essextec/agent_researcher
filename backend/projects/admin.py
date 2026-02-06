from django.contrib import admin
from .models import Project, Iteration, WorkProduct, Annotation


class IterationInline(admin.TabularInline):
    model = Iteration
    extra = 0
    readonly_fields = ('id', 'sequence', 'status', 'created_at')
    fields = ('sequence', 'name', 'status', 'created_at')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_name', 'context_mode', 'get_iteration_count', 'updated_at')
    list_filter = ('context_mode', 'created_at')
    search_fields = ('name', 'client_name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [IterationInline]

    def get_iteration_count(self, obj):
        return obj.iterations.count()
    get_iteration_count.short_description = 'Iterations'


@admin.register(Iteration)
class IterationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'project', 'sequence', 'status', 'created_at')
    list_filter = ('status', 'project', 'created_at')
    search_fields = ('name', 'project__name', 'project__client_name')
    readonly_fields = ('id', 'sequence', 'created_at')


@admin.register(WorkProduct)
class WorkProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'category', 'starred', 'source_iteration', 'created_at')
    list_filter = ('category', 'starred', 'project')
    search_fields = ('notes', 'project__name')
    readonly_fields = ('id', 'created_at')


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'text_preview', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('text', 'project__name')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Text'
