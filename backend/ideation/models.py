"""Models for the ideation loop module (Epic 4: AGE-18, AGE-19, AGE-20)."""
import uuid
from django.db import models
from research.models import ResearchJob


class UseCase(models.Model):
    """AI/technology use case generated during ideation (AGE-18)."""

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('refined', 'Refined'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    research_job = models.ForeignKey(
        ResearchJob,
        on_delete=models.CASCADE,
        related_name='use_cases',
    )

    # Use case details
    title = models.CharField(max_length=255)
    description = models.TextField()
    business_problem = models.TextField(help_text="The business problem this addresses")
    proposed_solution = models.TextField(help_text="AI/technology solution overview")

    # Value proposition
    expected_benefits = models.JSONField(default=list, blank=True)
    estimated_roi = models.CharField(max_length=100, blank=True)
    time_to_value = models.CharField(max_length=100, blank=True)

    # Technical assessment
    technologies = models.JSONField(default=list, blank=True)
    data_requirements = models.JSONField(default=list, blank=True)
    integration_points = models.JSONField(default=list, blank=True)

    # Prioritization
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    impact_score = models.FloatField(default=0.0)
    feasibility_score = models.FloatField(default=0.0)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-impact_score', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"


class FeasibilityAssessment(models.Model):
    """Technical feasibility assessment for a use case (AGE-19)."""

    FEASIBILITY_LEVELS = [
        ('low', 'Low - Significant challenges'),
        ('medium', 'Medium - Some challenges'),
        ('high', 'High - Readily achievable'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    use_case = models.OneToOneField(
        UseCase,
        on_delete=models.CASCADE,
        related_name='feasibility_assessment',
    )

    # Overall assessment
    overall_feasibility = models.CharField(
        max_length=20,
        choices=FEASIBILITY_LEVELS,
        default='medium',
    )
    overall_score = models.FloatField(default=0.0)

    # Technical factors
    technical_complexity = models.TextField(blank=True)
    data_availability = models.TextField(blank=True)
    integration_complexity = models.TextField(blank=True)
    scalability_considerations = models.TextField(blank=True)

    # Risk assessment
    technical_risks = models.JSONField(default=list, blank=True)
    mitigation_strategies = models.JSONField(default=list, blank=True)

    # Prerequisites
    prerequisites = models.JSONField(default=list, blank=True)
    dependencies = models.JSONField(default=list, blank=True)

    # Recommendations
    recommendations = models.TextField(blank=True)
    next_steps = models.JSONField(default=list, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feasibility: {self.use_case.title} ({self.overall_feasibility})"


class RefinedPlay(models.Model):
    """Refined sales play generated from use case (AGE-20)."""

    PLAY_STATUS = [
        ('draft', 'Draft'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    use_case = models.OneToOneField(
        UseCase,
        on_delete=models.CASCADE,
        related_name='refined_play',
    )

    # Play content
    title = models.CharField(max_length=255)
    elevator_pitch = models.TextField(help_text="30-second pitch")
    value_proposition = models.TextField()
    key_differentiators = models.JSONField(default=list, blank=True)

    # Target audience
    target_persona = models.CharField(max_length=255, blank=True)
    target_vertical = models.CharField(max_length=100, blank=True)
    company_size_fit = models.CharField(max_length=100, blank=True)

    # Sales enablement
    discovery_questions = models.JSONField(default=list, blank=True)
    objection_handlers = models.JSONField(default=list, blank=True)
    proof_points = models.JSONField(default=list, blank=True)
    competitive_positioning = models.TextField(blank=True)

    # Call to action
    next_steps = models.JSONField(default=list, blank=True)
    success_metrics = models.JSONField(default=list, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=PLAY_STATUS, default='draft')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Refined plays'

    def __str__(self):
        return f"Play: {self.title} ({self.status})"
