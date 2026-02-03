"""Play refiner service (AGE-20)."""
import json
import logging
from typing import Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RefinedPlayData:
    """Data structure for a refined sales play."""
    title: str = ""
    elevator_pitch: str = ""
    value_proposition: str = ""
    key_differentiators: list = field(default_factory=list)
    target_persona: str = ""
    target_vertical: str = ""
    company_size_fit: str = ""
    discovery_questions: list = field(default_factory=list)
    objection_handlers: list = field(default_factory=list)
    proof_points: list = field(default_factory=list)
    competitive_positioning: str = ""
    next_steps: list = field(default_factory=list)
    success_metrics: list = field(default_factory=list)


class PlayRefiner:
    """Service to refine use cases into actionable sales plays."""

    PLAY_REFINER_PROMPT = '''You are a sales enablement expert creating a sales play from a use case.

Use Case:
- Title: {title}
- Description: {description}
- Business Problem: {business_problem}
- Proposed Solution: {proposed_solution}
- Expected Benefits: {expected_benefits}
- ROI: {estimated_roi}
- Time to Value: {time_to_value}

Company Context:
- Company: {client_name}
- Industry: {vertical}
- Digital Maturity: {digital_maturity}

Feasibility:
- Overall: {feasibility}
- Risks: {risks}
- Recommendations: {recommendations}

Create a refined sales play for this use case.

Respond with valid JSON:
{{
    "title": "Play title",
    "elevator_pitch": "30-second pitch capturing the value proposition",
    "value_proposition": "Detailed value proposition",
    "key_differentiators": ["Differentiator 1", "Differentiator 2"],
    "target_persona": "Target buyer persona",
    "target_vertical": "Target industry vertical",
    "company_size_fit": "Enterprise/Mid-market/SMB",
    "discovery_questions": [
        "Question 1?",
        "Question 2?"
    ],
    "objection_handlers": [
        {{"objection": "Objection 1", "response": "Response 1"}},
        {{"objection": "Objection 2", "response": "Response 2"}}
    ],
    "proof_points": ["Proof point 1", "Proof point 2"],
    "competitive_positioning": "How to position against competitors",
    "next_steps": ["Step 1", "Step 2"],
    "success_metrics": ["Metric 1", "Metric 2"]
}}

IMPORTANT:
- Make the elevator pitch compelling and concise
- Include 3-5 discovery questions
- Include 2-3 objection handlers
- Be specific to the company and use case
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

    def refine_play(self, use_case) -> RefinedPlayData:
        """Refine a use case into a sales play.

        Args:
            use_case: UseCase model instance

        Returns:
            RefinedPlayData object
        """
        research_job = use_case.research_job
        report = getattr(research_job, 'report', None)
        assessment = getattr(use_case, 'feasibility_assessment', None)

        context = {
            'title': use_case.title,
            'description': use_case.description,
            'business_problem': use_case.business_problem,
            'proposed_solution': use_case.proposed_solution,
            'expected_benefits': ', '.join(use_case.expected_benefits) if use_case.expected_benefits else 'Not specified',
            'estimated_roi': use_case.estimated_roi or 'Not specified',
            'time_to_value': use_case.time_to_value or 'Not specified',
            'client_name': research_job.client_name,
            'vertical': research_job.vertical or 'unknown',
            'digital_maturity': report.digital_maturity if report else 'unknown',
            'feasibility': assessment.overall_feasibility if assessment else 'Not assessed',
            'risks': ', '.join(assessment.technical_risks[:3]) if assessment and assessment.technical_risks else 'Not assessed',
            'recommendations': assessment.recommendations if assessment else 'Not assessed',
        }

        prompt = self.PLAY_REFINER_PROMPT.format(**context)

        try:
            response = self.gemini_client.generate_text(prompt)

            # Parse JSON response
            response_text = response.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            data = json.loads(response_text)

            # Handle objection_handlers format
            objection_handlers = []
            for oh in data.get('objection_handlers', []):
                if isinstance(oh, dict):
                    objection_handlers.append(oh)
                else:
                    objection_handlers.append({'objection': str(oh), 'response': ''})

            return RefinedPlayData(
                title=data.get('title', ''),
                elevator_pitch=data.get('elevator_pitch', ''),
                value_proposition=data.get('value_proposition', ''),
                key_differentiators=data.get('key_differentiators', []),
                target_persona=data.get('target_persona', ''),
                target_vertical=data.get('target_vertical', ''),
                company_size_fit=data.get('company_size_fit', ''),
                discovery_questions=data.get('discovery_questions', []),
                objection_handlers=objection_handlers,
                proof_points=data.get('proof_points', []),
                competitive_positioning=data.get('competitive_positioning', ''),
                next_steps=data.get('next_steps', []),
                success_metrics=data.get('success_metrics', []),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse play refiner response: {e}")
            return RefinedPlayData(title=use_case.title)
        except Exception as e:
            logger.exception("Error during play refinement")
            return RefinedPlayData(title=use_case.title)

    def create_play_model(self, use_case, play_data: RefinedPlayData):
        """Create RefinedPlay model instance.

        Args:
            use_case: The UseCase instance
            play_data: RefinedPlayData object

        Returns:
            Created RefinedPlay instance
        """
        from ..models import RefinedPlay

        play, created = RefinedPlay.objects.update_or_create(
            use_case=use_case,
            defaults={
                'title': play_data.title,
                'elevator_pitch': play_data.elevator_pitch,
                'value_proposition': play_data.value_proposition,
                'key_differentiators': play_data.key_differentiators,
                'target_persona': play_data.target_persona,
                'target_vertical': play_data.target_vertical,
                'company_size_fit': play_data.company_size_fit,
                'discovery_questions': play_data.discovery_questions,
                'objection_handlers': play_data.objection_handlers,
                'proof_points': play_data.proof_points,
                'competitive_positioning': play_data.competitive_positioning,
                'next_steps': play_data.next_steps,
                'success_metrics': play_data.success_metrics,
            }
        )

        # Update use case status
        use_case.status = 'refined'
        use_case.save(update_fields=['status'])

        return play
