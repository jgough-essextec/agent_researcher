"""Persona generation service (AGE-21)."""
import json
import logging
from typing import List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PersonaData:
    """Data structure for a buyer persona."""
    name: str = ""
    title: str = ""
    department: str = ""
    seniority_level: str = ""
    background: str = ""
    goals: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    motivations: List[str] = field(default_factory=list)
    decision_criteria: List[str] = field(default_factory=list)
    preferred_communication: str = ""
    objections: List[str] = field(default_factory=list)
    content_preferences: List[str] = field(default_factory=list)
    key_messages: List[str] = field(default_factory=list)


class PersonaGenerator:
    """Service to generate buyer personas from research."""

    PERSONA_PROMPT = '''You are a sales strategy expert creating buyer personas.

Based on the following research:
- Company: {client_name}
- Industry: {vertical}
- Decision Makers: {decision_makers}
- Pain Points: {pain_points}
- Strategic Goals: {strategic_goals}
- Digital Maturity: {digital_maturity}

Generate 2-3 detailed buyer personas for key stakeholders at this company.

Respond with valid JSON:
{{
    "personas": [
        {{
            "name": "Persona name (e.g., 'The Tech-Forward CTO')",
            "title": "Job title",
            "department": "Department",
            "seniority_level": "C-Level/VP/Director/Manager",
            "background": "Brief professional background",
            "goals": ["Goal 1", "Goal 2"],
            "challenges": ["Challenge 1", "Challenge 2"],
            "motivations": ["Motivation 1", "Motivation 2"],
            "decision_criteria": ["Criteria 1", "Criteria 2"],
            "preferred_communication": "Email/Phone/In-person/Video",
            "objections": ["Common objection 1", "Common objection 2"],
            "content_preferences": ["Whitepapers", "Case studies", "Demos"],
            "key_messages": ["Message that resonates 1", "Message 2"]
        }}
    ]
}}

IMPORTANT:
- Create 2-3 distinct personas
- Make them specific to this company and industry
- Include realistic objections and how to address them
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

    def generate_personas(self, research_job) -> List[PersonaData]:
        """Generate personas from a completed research job.

        Args:
            research_job: ResearchJob model instance

        Returns:
            List of PersonaData objects
        """
        report = getattr(research_job, 'report', None)

        # Format decision makers
        decision_makers = "Not identified"
        if report and report.decision_makers:
            dms = []
            for dm in report.decision_makers[:5]:
                if isinstance(dm, dict):
                    dms.append(f"{dm.get('name', '')} ({dm.get('title', '')})")
                else:
                    dms.append(str(dm))
            decision_makers = ', '.join(dms)

        context = {
            'client_name': research_job.client_name,
            'vertical': research_job.vertical or 'unknown',
            'decision_makers': decision_makers,
            'pain_points': ', '.join(report.pain_points[:5]) if report and report.pain_points else 'Not identified',
            'strategic_goals': ', '.join(report.strategic_goals[:5]) if report and report.strategic_goals else 'Not identified',
            'digital_maturity': report.digital_maturity if report else 'unknown',
        }

        prompt = self.PERSONA_PROMPT.format(**context)

        try:
            response = self.gemini_client.generate_text(prompt)

            # Parse JSON response
            response_text = response.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            data = json.loads(response_text)
            personas = []

            for p in data.get('personas', []):
                personas.append(PersonaData(
                    name=p.get('name', ''),
                    title=p.get('title', ''),
                    department=p.get('department', ''),
                    seniority_level=p.get('seniority_level', ''),
                    background=p.get('background', ''),
                    goals=p.get('goals', []),
                    challenges=p.get('challenges', []),
                    motivations=p.get('motivations', []),
                    decision_criteria=p.get('decision_criteria', []),
                    preferred_communication=p.get('preferred_communication', ''),
                    objections=p.get('objections', []),
                    content_preferences=p.get('content_preferences', []),
                    key_messages=p.get('key_messages', []),
                ))

            return personas

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse persona response: {e}")
            return []
        except Exception as e:
            logger.exception("Error during persona generation")
            return []

    def create_persona_models(self, research_job, personas: List[PersonaData]):
        """Create Persona model instances.

        Args:
            research_job: The ResearchJob instance
            personas: List of PersonaData objects

        Returns:
            List of created Persona instances
        """
        from ..models import Persona

        created = []
        for p_data in personas:
            persona = Persona.objects.create(
                research_job=research_job,
                name=p_data.name,
                title=p_data.title,
                department=p_data.department,
                seniority_level=p_data.seniority_level,
                background=p_data.background,
                goals=p_data.goals,
                challenges=p_data.challenges,
                motivations=p_data.motivations,
                decision_criteria=p_data.decision_criteria,
                preferred_communication=p_data.preferred_communication,
                objections=p_data.objections,
                content_preferences=p_data.content_preferences,
                key_messages=p_data.key_messages,
            )
            created.append(persona)

        return created
