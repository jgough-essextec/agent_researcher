"""Serializers for the projects app."""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from .models import Project, Iteration, WorkProduct, Annotation


class AnnotationSerializer(serializers.ModelSerializer):
    """Serializer for Annotation model."""

    content_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Annotation
        fields = [
            'id', 'project', 'content_type', 'content_type_name',
            'object_id', 'text', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_content_type_name(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"


class WorkProductSerializer(serializers.ModelSerializer):
    """Serializer for WorkProduct model."""

    content_type_name = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()
    source_iteration_sequence = serializers.SerializerMethodField()

    class Meta:
        model = WorkProduct
        fields = [
            'id', 'project', 'content_type', 'content_type_name',
            'object_id', 'content_preview', 'source_iteration',
            'source_iteration_sequence', 'category', 'starred',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_content_type_name(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    def get_content_preview(self, obj):
        """Get a preview of the content object."""
        try:
            content = obj.content_object
            if content is None:
                return None

            # Try common fields
            preview = {}
            for field in ['title', 'name', 'headline']:
                if hasattr(content, field):
                    preview['title'] = getattr(content, field)
                    break

            for field in ['description', 'summary', 'executive_summary']:
                if hasattr(content, field):
                    text = getattr(content, field)
                    preview['summary'] = text[:200] + '...' if len(text) > 200 else text
                    break

            return preview
        except Exception:
            return None

    def get_source_iteration_sequence(self, obj):
        if obj.source_iteration:
            return obj.source_iteration.sequence
        return None


class IterationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing iterations."""

    has_research_job = serializers.SerializerMethodField()

    class Meta:
        model = Iteration
        fields = [
            'id', 'sequence', 'name', 'status',
            'has_research_job', 'created_at'
        ]
        read_only_fields = ['id', 'sequence', 'created_at']

    def get_has_research_job(self, obj):
        return hasattr(obj, 'research_job') and obj.research_job is not None


class IterationDetailSerializer(serializers.ModelSerializer):
    """Full serializer for iteration details."""

    research_job_id = serializers.SerializerMethodField()
    research_job_status = serializers.SerializerMethodField()
    work_products = WorkProductSerializer(many=True, read_only=True)

    class Meta:
        model = Iteration
        fields = [
            'id', 'project', 'sequence', 'name', 'sales_history',
            'prompt_override', 'status', 'inherited_context',
            'research_job_id', 'research_job_status',
            'work_products', 'created_at'
        ]
        read_only_fields = ['id', 'sequence', 'inherited_context', 'created_at']

    def get_research_job_id(self, obj):
        if hasattr(obj, 'research_job') and obj.research_job:
            return str(obj.research_job.id)
        return None

    def get_research_job_status(self, obj):
        if hasattr(obj, 'research_job') and obj.research_job:
            return obj.research_job.status
        return None


class IterationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new iterations."""

    class Meta:
        model = Iteration
        fields = [
            'id', 'project', 'name', 'sales_history', 'prompt_override'
        ]
        read_only_fields = ['id']


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing projects."""

    iteration_count = serializers.IntegerField(read_only=True)
    latest_iteration_status = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'client_name', 'context_mode',
            'iteration_count', 'latest_iteration_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_latest_iteration_status(self, obj):
        latest = obj.latest_iteration
        if latest:
            return latest.status
        return None


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Full serializer for project details."""

    iterations = IterationListSerializer(many=True, read_only=True)
    work_products_count = serializers.SerializerMethodField()
    annotations_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'client_name', 'description', 'context_mode',
            'iterations', 'work_products_count', 'annotations_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_work_products_count(self, obj):
        return obj.work_products.count()

    def get_annotations_count(self, obj):
        return obj.annotations.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new projects."""

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'client_name', 'description', 'context_mode'
        ]
        read_only_fields = ['id']


class WorkProductCreateSerializer(serializers.Serializer):
    """Serializer for creating work products with content type resolution."""

    content_type = serializers.CharField(
        help_text="Format: app_label.model (e.g., ideation.refinedplay)"
    )
    object_id = serializers.UUIDField()
    source_iteration_id = serializers.UUIDField(required=False, allow_null=True)
    category = serializers.ChoiceField(choices=WorkProduct.CATEGORY_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_content_type(self, value):
        """Resolve content type string to ContentType object."""
        try:
            app_label, model = value.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model)
            return ct
        except ValueError:
            raise serializers.ValidationError(
                "Content type must be in format 'app_label.model'"
            )
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(
                f"Content type '{value}' does not exist"
            )

    def create(self, validated_data):
        project = self.context['project']
        source_iteration_id = validated_data.pop('source_iteration_id', None)

        source_iteration = None
        if source_iteration_id:
            try:
                source_iteration = Iteration.objects.get(
                    id=source_iteration_id,
                    project=project
                )
            except Iteration.DoesNotExist:
                pass

        return WorkProduct.objects.create(
            project=project,
            source_iteration=source_iteration,
            **validated_data
        )


class AnnotationCreateSerializer(serializers.Serializer):
    """Serializer for creating annotations with content type resolution."""

    content_type = serializers.CharField(
        help_text="Format: app_label.model (e.g., research.researchreport)"
    )
    object_id = serializers.UUIDField()
    text = serializers.CharField()

    def validate_content_type(self, value):
        """Resolve content type string to ContentType object."""
        try:
            app_label, model = value.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model)
            return ct
        except ValueError:
            raise serializers.ValidationError(
                "Content type must be in format 'app_label.model'"
            )
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(
                f"Content type '{value}' does not exist"
            )

    def create(self, validated_data):
        project = self.context['project']
        return Annotation.objects.create(project=project, **validated_data)


class TimelineSerializer(serializers.Serializer):
    """Serializer for timeline view data."""

    iterations = serializers.SerializerMethodField()
    work_products_by_iteration = serializers.SerializerMethodField()

    def get_iterations(self, project):
        iterations = project.iterations.all()
        return IterationListSerializer(iterations, many=True).data

    def get_work_products_by_iteration(self, project):
        """Group work products by source iteration."""
        work_products = project.work_products.select_related('source_iteration')

        grouped = {}
        for wp in work_products:
            seq = wp.source_iteration.sequence if wp.source_iteration else 0
            if seq not in grouped:
                grouped[seq] = []
            grouped[seq].append(WorkProductSerializer(wp).data)

        return grouped


class CompareSerializer(serializers.Serializer):
    """Serializer for iteration comparison request."""

    iteration_a = serializers.IntegerField(help_text="First iteration sequence number")
    iteration_b = serializers.IntegerField(help_text="Second iteration sequence number")
