"""Models for the project-based iterative workflow."""
import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Project(models.Model):
    """Top-level engagement wrapper for iterative research."""

    CONTEXT_MODE_CHOICES = [
        ('accumulate', 'Build on Previous'),
        ('fresh', 'Fresh Start'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    context_mode = models.CharField(
        max_length=20,
        choices=CONTEXT_MODE_CHOICES,
        default='accumulate',
        help_text='How iterations build on each other',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.client_name})"

    @property
    def latest_iteration(self):
        """Return the most recent iteration."""
        return self.iterations.order_by('-sequence').first()

    def get_iteration_count(self):
        """Return the number of iterations."""
        return self.iterations.count()


class Iteration(models.Model):
    """A single research iteration within a project."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='iterations',
    )
    sequence = models.PositiveIntegerField(
        help_text='Iteration number (1, 2, 3...)',
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Optional label like "v2 - Focus on AI"',
    )
    sales_history = models.TextField(blank=True)
    prompt_override = models.TextField(
        blank=True,
        help_text='Additional guidance for this iteration',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )

    # Inherited context from previous iteration (if context_mode='accumulate')
    inherited_context = models.JSONField(
        default=dict,
        blank=True,
        help_text='Context inherited from previous iteration',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence']
        unique_together = ['project', 'sequence']

    def __str__(self):
        label = self.name or f"Iteration {self.sequence}"
        return f"{self.project.name} - {label}"

    def save(self, *args, **kwargs):
        # Auto-assign sequence number if not set
        if not self.sequence:
            max_seq = Iteration.objects.filter(project=self.project).aggregate(
                models.Max('sequence')
            )['sequence__max']
            self.sequence = (max_seq or 0) + 1
        super().save(*args, **kwargs)


class WorkProduct(models.Model):
    """Items starred/saved as 'keepers' across iterations."""

    CATEGORY_CHOICES = [
        ('play', 'Refined Play'),
        ('persona', 'Persona'),
        ('insight', 'Insight'),
        ('one_pager', 'One Pager'),
        ('case_study', 'Case Study'),
        ('use_case', 'Use Case'),
        ('gap', 'Gap Analysis'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='work_products',
    )

    # Generic FK to any model (RefinedPlay, Persona, OnePager, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    source_iteration = models.ForeignKey(
        Iteration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_products',
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
    )
    starred = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category}: {self.content_object}"


class Annotation(models.Model):
    """User notes attached to any object."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='annotations',
    )

    # Generic FK
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.content_object}: {self.text[:50]}"
