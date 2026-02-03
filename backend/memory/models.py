"""Models for the memory/vector knowledge base module (Epic 3: AGE-14, AGE-15, AGE-16)."""
import uuid
from django.db import models


class ClientProfile(models.Model):
    """Client profile stored in vector database for context retrieval (AGE-15)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_name = models.CharField(max_length=255, unique=True)

    # Profile data
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    region = models.CharField(max_length=100, blank=True)
    key_contacts = models.JSONField(default=list, blank=True)

    # Summary for embedding
    summary = models.TextField(blank=True)

    # Vector store reference
    vector_id = models.CharField(max_length=255, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Profile: {self.client_name}"


class SalesPlay(models.Model):
    """Sales play/strategy stored for retrieval and reuse (AGE-16)."""

    PLAY_TYPES = [
        ('pitch', 'Pitch'),
        ('objection_handler', 'Objection Handler'),
        ('value_proposition', 'Value Proposition'),
        ('case_study', 'Case Study'),
        ('competitive_response', 'Competitive Response'),
        ('discovery_question', 'Discovery Question'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    play_type = models.CharField(max_length=50, choices=PLAY_TYPES)

    # Content
    content = models.TextField()
    context = models.TextField(blank=True, help_text="When to use this play")
    industry = models.CharField(max_length=100, blank=True)
    vertical = models.CharField(max_length=50, blank=True)

    # Effectiveness tracking
    usage_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)

    # Vector store reference
    vector_id = models.CharField(max_length=255, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-success_rate', '-usage_count']
        verbose_name_plural = 'Sales plays'

    def __str__(self):
        return f"{self.play_type}: {self.title}"


class MemoryEntry(models.Model):
    """Generic memory entry for storing various types of knowledge (AGE-17)."""

    ENTRY_TYPES = [
        ('research_insight', 'Research Insight'),
        ('client_interaction', 'Client Interaction'),
        ('deal_outcome', 'Deal Outcome'),
        ('best_practice', 'Best Practice'),
        ('lesson_learned', 'Lesson Learned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry_type = models.CharField(max_length=50, choices=ENTRY_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()

    # Context
    client_name = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Source reference
    source_type = models.CharField(max_length=50, blank=True)
    source_id = models.CharField(max_length=255, blank=True)

    # Vector store reference
    vector_id = models.CharField(max_length=255, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Memory entries'

    def __str__(self):
        return f"{self.entry_type}: {self.title}"
