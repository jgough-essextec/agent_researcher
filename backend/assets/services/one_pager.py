"""One-pager generation service (AGE-22)."""
import json
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class OnePagerData:
    """Data structure for a one-pager document."""
    title: str = ""
    headline: str = ""
    executive_summary: str = ""
    challenge_section: str = ""
    solution_section: str = ""
    benefits_section: str = ""
    differentiators: List[str] = field(default_factory=list)
    call_to_action: str = ""
    next_steps: List[str] = field(default_factory=list)


class OnePagerGenerator:
    """Service to generate one-pager sales documents."""

    ONE_PAGER_PROMPT = '''You are a sales content expert creating a one-page sales document.

Based on the following:
- Company: {client_name}
- Industry: {vertical}
- Pain Points: {pain_points}
- Opportunities: {opportunities}
- Use Case: {use_case_title}
- Solution: {proposed_solution}
- Benefits: {expected_benefits}

Create a compelling one-pager sales document.

Respond with valid JSON:
{{
    "title": "Document title",
    "headline": "Compelling headline that captures the value proposition",
    "executive_summary": "2-3 sentence executive summary",
    "challenge_section": "Description of the business challenges this addresses",
    "solution_section": "How the solution addresses the challenges",
    "benefits_section": "Key benefits and outcomes",
    "differentiators": ["Differentiator 1", "Differentiator 2", "Differentiator 3"],
    "call_to_action": "Clear call to action",
    "next_steps": ["Step 1", "Step 2", "Step 3"]
}}

IMPORTANT:
- Keep content concise but compelling
- Focus on customer outcomes, not features
- Make it specific to this company
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

    def generate_one_pager(self, research_job, use_case=None) -> OnePagerData:
        """Generate a one-pager from research and optional use case.

        Args:
            research_job: ResearchJob model instance
            use_case: Optional UseCase model instance

        Returns:
            OnePagerData object
        """
        report = getattr(research_job, 'report', None)

        context = {
            'client_name': research_job.client_name,
            'vertical': research_job.vertical or 'unknown',
            'pain_points': ', '.join(report.pain_points[:5]) if report and report.pain_points else 'Not identified',
            'opportunities': ', '.join(report.opportunities[:3]) if report and report.opportunities else 'Not identified',
            'use_case_title': use_case.title if use_case else 'General AI/Technology Solution',
            'proposed_solution': use_case.proposed_solution if use_case else 'AI-powered solutions',
            'expected_benefits': ', '.join(use_case.expected_benefits) if use_case and use_case.expected_benefits else 'Improved efficiency and outcomes',
        }

        prompt = self.ONE_PAGER_PROMPT.format(**context)

        try:
            response = self.gemini_client.generate_text(prompt)

            # Parse JSON response
            response_text = response.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            data = json.loads(response_text)

            return OnePagerData(
                title=data.get('title', ''),
                headline=data.get('headline', ''),
                executive_summary=data.get('executive_summary', ''),
                challenge_section=data.get('challenge_section', ''),
                solution_section=data.get('solution_section', ''),
                benefits_section=data.get('benefits_section', ''),
                differentiators=data.get('differentiators', []),
                call_to_action=data.get('call_to_action', ''),
                next_steps=data.get('next_steps', []),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse one-pager response: {e}")
            return OnePagerData(title=f"One-Pager for {research_job.client_name}")
        except Exception as e:
            logger.exception("Error during one-pager generation")
            return OnePagerData(title=f"One-Pager for {research_job.client_name}")

    def create_one_pager_model(self, research_job, one_pager_data: OnePagerData):
        """Create OnePager model instance.

        Args:
            research_job: The ResearchJob instance
            one_pager_data: OnePagerData object

        Returns:
            Created OnePager instance
        """
        from ..models import OnePager

        one_pager = OnePager.objects.create(
            research_job=research_job,
            title=one_pager_data.title,
            headline=one_pager_data.headline,
            executive_summary=one_pager_data.executive_summary,
            challenge_section=one_pager_data.challenge_section,
            solution_section=one_pager_data.solution_section,
            benefits_section=one_pager_data.benefits_section,
            differentiators=one_pager_data.differentiators,
            call_to_action=one_pager_data.call_to_action,
            next_steps=one_pager_data.next_steps,
        )

        return one_pager
