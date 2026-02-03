"""Models for the asset generation module (Epic 5: AGE-21, AGE-22, AGE-23, AGE-24)."""
import uuid
from django.db import models
from research.models import ResearchJob


class Persona(models.Model):
    """Buyer persona generated from research (AGE-21)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    research_job = models.ForeignKey(
        ResearchJob,
        on_delete=models.CASCADE,
        related_name='personas',
    )

    # Persona identity
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True)
    seniority_level = models.CharField(max_length=50, blank=True)

    # Demographics
    background = models.TextField(blank=True)
    goals = models.JSONField(default=list, blank=True)
    challenges = models.JSONField(default=list, blank=True)
    motivations = models.JSONField(default=list, blank=True)

    # Buying behavior
    decision_criteria = models.JSONField(default=list, blank=True)
    preferred_communication = models.CharField(max_length=100, blank=True)
    objections = models.JSONField(default=list, blank=True)

    # Content preferences
    content_preferences = models.JSONField(default=list, blank=True)
    key_messages = models.JSONField(default=list, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.title}"


class OnePager(models.Model):
    """One-page sales document (AGE-22)."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('shared', 'Shared'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    research_job = models.ForeignKey(
        ResearchJob,
        on_delete=models.CASCADE,
        related_name='one_pagers',
    )

    # Document content
    title = models.CharField(max_length=255)
    headline = models.CharField(max_length=500)
    executive_summary = models.TextField()

    # Key sections
    challenge_section = models.TextField()
    solution_section = models.TextField()
    benefits_section = models.TextField()
    differentiators = models.JSONField(default=list, blank=True)

    # Call to action
    call_to_action = models.TextField(blank=True)
    next_steps = models.JSONField(default=list, blank=True)

    # Export
    html_content = models.TextField(blank=True)
    pdf_path = models.CharField(max_length=500, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'One pagers'

    def __str__(self):
        return f"One-Pager: {self.title}"


class AccountPlan(models.Model):
    """Strategic account plan document (AGE-23)."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('active', 'Active'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    research_job = models.OneToOneField(
        ResearchJob,
        on_delete=models.CASCADE,
        related_name='account_plan',
    )

    # Executive summary
    title = models.CharField(max_length=255)
    executive_summary = models.TextField()

    # Account overview
    account_overview = models.TextField()
    strategic_objectives = models.JSONField(default=list, blank=True)
    key_stakeholders = models.JSONField(default=list, blank=True)

    # Opportunity analysis
    opportunities = models.JSONField(default=list, blank=True)
    competitive_landscape = models.TextField(blank=True)
    swot_analysis = models.JSONField(default=dict, blank=True)

    # Strategy
    engagement_strategy = models.TextField(blank=True)
    value_propositions = models.JSONField(default=list, blank=True)
    action_plan = models.JSONField(default=list, blank=True)

    # Success metrics
    success_metrics = models.JSONField(default=list, blank=True)
    milestones = models.JSONField(default=list, blank=True)
    timeline = models.TextField(blank=True)

    # Export
    html_content = models.TextField(blank=True)
    pdf_path = models.CharField(max_length=500, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Account Plan: {self.title}"


class Citation(models.Model):
    """Source citation for generated content (AGE-24)."""

    CITATION_TYPES = [
        ('news', 'News Article'),
        ('website', 'Company Website'),
        ('report', 'Industry Report'),
        ('social', 'Social Media'),
        ('financial', 'Financial Filing'),
        ('press_release', 'Press Release'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    research_job = models.ForeignKey(
        ResearchJob,
        on_delete=models.CASCADE,
        related_name='citations',
    )

    # Citation details
    citation_type = models.CharField(max_length=50, choices=CITATION_TYPES)
    title = models.CharField(max_length=500)
    source = models.CharField(max_length=255)
    url = models.URLField(blank=True)
    author = models.CharField(max_length=255, blank=True)
    publication_date = models.DateField(null=True, blank=True)

    # Content
    excerpt = models.TextField(blank=True)
    relevance_note = models.TextField(blank=True)

    # Verification
    verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.citation_type}: {self.title[:50]}"
