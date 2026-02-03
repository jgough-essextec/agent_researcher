"""Feasibility assessment service (AGE-19)."""
import json
import logging
from typing import Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FeasibilityData:
    """Data structure for feasibility assessment."""
    overall_feasibility: str = "medium"
    overall_score: float = 0.0
    technical_complexity: str = ""
    data_availability: str = ""
    integration_complexity: str = ""
    scalability_considerations: str = ""
    technical_risks: list = field(default_factory=list)
    mitigation_strategies: list = field(default_factory=list)
    prerequisites: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)
    recommendations: str = ""
    next_steps: list = field(default_factory=list)


class FeasibilityService:
    """Service to assess technical feasibility of use cases."""

    FEASIBILITY_PROMPT = '''You are a technical architect assessing the feasibility of an AI use case.

Use Case:
- Title: {title}
- Description: {description}
- Business Problem: {business_problem}
- Proposed Solution: {proposed_solution}
- Technologies: {technologies}
- Data Requirements: {data_requirements}
- Integration Points: {integration_points}

Company Context:
- Industry: {vertical}
- Digital Maturity: {digital_maturity}
- AI Adoption Stage: {ai_adoption_stage}

Assess the technical feasibility of this use case.

Respond with valid JSON:
{{
    "overall_feasibility": "low|medium|high",
    "overall_score": 0.75,
    "technical_complexity": "Assessment of technical complexity",
    "data_availability": "Assessment of data readiness",
    "integration_complexity": "Assessment of integration needs",
    "scalability_considerations": "Scalability factors to consider",
    "technical_risks": [
        "Risk 1",
        "Risk 2"
    ],
    "mitigation_strategies": [
        "Strategy 1",
        "Strategy 2"
    ],
    "prerequisites": [
        "Prerequisite 1",
        "Prerequisite 2"
    ],
    "dependencies": [
        "Dependency 1",
        "Dependency 2"
    ],
    "recommendations": "Overall recommendations",
    "next_steps": [
        "Step 1",
        "Step 2"
    ]
}}

IMPORTANT:
- Be realistic about technical challenges
- Consider the company's current maturity level
- overall_score should be 0.0-1.0
- Respond ONLY with valid JSON
'''

    def __init__(self, gemini_client=None):
        """Initialize with optional Gemini client."""
        self._gemini_client = gemini_client

    @property
    def gemini_client(self):
        """Lazy initialization of Gemini client."""
        if self._gemini_client is None:
            from research.services.gemini import GeminiClient
            self._gemini_client = GeminiClient()
        return self._gemini_client

    def assess_feasibility(self, use_case) -> FeasibilityData:
        """Assess feasibility of a use case.

        Args:
            use_case: UseCase model instance

        Returns:
            FeasibilityData object
        """
        research_job = use_case.research_job
        report = getattr(research_job, 'report', None)

        context = {
            'title': use_case.title,
            'description': use_case.description,
            'business_problem': use_case.business_problem,
            'proposed_solution': use_case.proposed_solution,
            'technologies': ', '.join(use_case.technologies) if use_case.technologies else 'Not specified',
            'data_requirements': ', '.join(use_case.data_requirements) if use_case.data_requirements else 'Not specified',
            'integration_points': ', '.join(use_case.integration_points) if use_case.integration_points else 'Not specified',
            'vertical': research_job.vertical or 'unknown',
            'digital_maturity': report.digital_maturity if report else 'unknown',
            'ai_adoption_stage': report.ai_adoption_stage if report else 'unknown',
        }

        prompt = self.FEASIBILITY_PROMPT.format(**context)

        try:
            response = self.gemini_client.generate_text(prompt)

            # Parse JSON response
            response_text = response.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            data = json.loads(response_text)

            return FeasibilityData(
                overall_feasibility=data.get('overall_feasibility', 'medium'),
                overall_score=float(data.get('overall_score', 0.0)),
                technical_complexity=data.get('technical_complexity', ''),
                data_availability=data.get('data_availability', ''),
                integration_complexity=data.get('integration_complexity', ''),
                scalability_considerations=data.get('scalability_considerations', ''),
                technical_risks=data.get('technical_risks', []),
                mitigation_strategies=data.get('mitigation_strategies', []),
                prerequisites=data.get('prerequisites', []),
                dependencies=data.get('dependencies', []),
                recommendations=data.get('recommendations', ''),
                next_steps=data.get('next_steps', []),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse feasibility response: {e}")
            return FeasibilityData(recommendations=f"Assessment failed: {str(e)}")
        except Exception as e:
            logger.exception("Error during feasibility assessment")
            return FeasibilityData(recommendations=f"Assessment failed: {str(e)}")

    def create_assessment_model(self, use_case, feasibility_data: FeasibilityData):
        """Create FeasibilityAssessment model instance.

        Args:
            use_case: The UseCase instance
            feasibility_data: FeasibilityData object

        Returns:
            Created FeasibilityAssessment instance
        """
        from ..models import FeasibilityAssessment

        assessment, created = FeasibilityAssessment.objects.update_or_create(
            use_case=use_case,
            defaults={
                'overall_feasibility': feasibility_data.overall_feasibility,
                'overall_score': feasibility_data.overall_score,
                'technical_complexity': feasibility_data.technical_complexity,
                'data_availability': feasibility_data.data_availability,
                'integration_complexity': feasibility_data.integration_complexity,
                'scalability_considerations': feasibility_data.scalability_considerations,
                'technical_risks': feasibility_data.technical_risks,
                'mitigation_strategies': feasibility_data.mitigation_strategies,
                'prerequisites': feasibility_data.prerequisites,
                'dependencies': feasibility_data.dependencies,
                'recommendations': feasibility_data.recommendations,
                'next_steps': feasibility_data.next_steps,
            }
        )

        # Update use case status
        use_case.status = 'validated'
        use_case.feasibility_score = feasibility_data.overall_score
        use_case.save(update_fields=['status', 'feasibility_score'])

        return assessment
