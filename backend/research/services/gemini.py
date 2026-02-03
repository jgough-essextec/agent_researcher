"""Gemini API client for deep research."""
import json
import logging
from typing import Optional
from dataclasses import dataclass, field, asdict
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class DecisionMaker:
    """A key decision maker at the company."""
    name: str = ""
    title: str = ""
    background: str = ""
    linkedin_url: str = ""


@dataclass
class NewsItem:
    """A recent news item about the company."""
    title: str = ""
    summary: str = ""
    date: str = ""
    source: str = ""
    url: str = ""


@dataclass
class ResearchReportData:
    """Structured data from deep research."""
    # Company overview
    company_overview: str = ""
    founded_year: Optional[int] = None
    headquarters: str = ""
    employee_count: str = ""
    annual_revenue: str = ""
    website: str = ""

    # Recent news
    recent_news: list = field(default_factory=list)

    # Decision makers
    decision_makers: list = field(default_factory=list)

    # Pain points and opportunities
    pain_points: list = field(default_factory=list)
    opportunities: list = field(default_factory=list)

    # Digital and AI assessment
    digital_maturity: str = ""
    ai_footprint: str = ""
    ai_adoption_stage: str = ""

    # Strategic information
    strategic_goals: list = field(default_factory=list)
    key_initiatives: list = field(default_factory=list)

    # Talking points
    talking_points: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for model storage."""
        return asdict(self)


class GeminiClient:
    """Client for Gemini API with structured output parsing."""

    DEEP_RESEARCH_PROMPT = '''You are a deep research assistant conducting comprehensive prospect research.

Given the following client information:
- Client Name: {client_name}
- Past Sales History: {sales_history}

Conduct thorough research and provide a comprehensive analysis. Your response MUST be valid JSON matching this exact structure:

{{
    "company_overview": "Comprehensive overview of the company, its business model, products/services, market position",
    "founded_year": 2000,
    "headquarters": "City, State/Country",
    "employee_count": "1,000-5,000",
    "annual_revenue": "$500M - $1B",
    "website": "https://example.com",
    "recent_news": [
        {{
            "title": "News headline",
            "summary": "Brief summary of the news",
            "date": "2024-01-15",
            "source": "News source name",
            "url": "https://source.com/article"
        }}
    ],
    "decision_makers": [
        {{
            "name": "Full Name",
            "title": "Job Title",
            "background": "Brief professional background",
            "linkedin_url": "https://linkedin.com/in/..."
        }}
    ],
    "pain_points": [
        "Pain point 1: description of business challenge or issue",
        "Pain point 2: another challenge they face"
    ],
    "opportunities": [
        "Opportunity 1: area where AI/technology could help",
        "Opportunity 2: another potential value-add"
    ],
    "digital_maturity": "nascent|developing|maturing|advanced|leading",
    "ai_footprint": "Description of their current AI/ML usage and capabilities",
    "ai_adoption_stage": "exploring|experimenting|implementing|scaling|optimizing",
    "strategic_goals": [
        "Strategic goal 1",
        "Strategic goal 2"
    ],
    "key_initiatives": [
        "Current initiative or transformation project 1",
        "Initiative 2"
    ],
    "talking_points": [
        "Specific talking point for sales conversation 1",
        "Talking point 2 with personalized angle"
    ]
}}

IMPORTANT:
- Respond ONLY with valid JSON, no additional text
- Include 3-5 items for each list field where possible
- Use "unknown" for fields you cannot determine
- For digital_maturity use one of: nascent, developing, maturing, advanced, leading
- For ai_adoption_stage use one of: exploring, experimenting, implementing, scaling, optimizing
- Be specific and actionable in pain points, opportunities, and talking points
'''

    VERTICAL_CLASSIFICATION_PROMPT = '''Based on the following company information, classify the company into one of these industry verticals:

Company: {client_name}
Overview: {company_overview}

Available verticals:
- healthcare: Healthcare, pharmaceuticals, medical devices, health services
- finance: Banking, insurance, investment, fintech
- retail: Retail, e-commerce, consumer goods
- manufacturing: Manufacturing, industrial, production
- technology: Software, IT services, tech products
- energy: Oil & gas, utilities, renewable energy
- telecommunications: Telecom, network services
- media_entertainment: Media, entertainment, gaming, publishing
- transportation: Logistics, shipping, airlines, automotive
- real_estate: Real estate, property management
- professional_services: Consulting, legal, accounting
- education: Education, EdTech, training
- government: Government, public sector
- hospitality: Hotels, restaurants, travel
- agriculture: Agriculture, food production
- construction: Construction, engineering
- nonprofit: Non-profit organizations
- other: Other industries

Respond with ONLY the vertical name (e.g., "healthcare" or "finance"), nothing else.
'''

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini client."""
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._client = None

    @property
    def client(self):
        """Lazy initialization of the Gemini client."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def conduct_deep_research(
        self,
        client_name: str,
        sales_history: str = "",
    ) -> ResearchReportData:
        """Conduct deep research and return structured data."""
        prompt = self.DEEP_RESEARCH_PROMPT.format(
            client_name=client_name,
            sales_history=sales_history or "No sales history provided",
        )

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Handle potential markdown code blocks
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                # Remove first and last lines (```json and ```)
                response_text = '\n'.join(lines[1:-1])

            data = json.loads(response_text)
            return ResearchReportData(**data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.debug(f"Raw response: {response.text}")
            # Return partial data with raw text in overview
            return ResearchReportData(
                company_overview=f"Research completed but structured parsing failed. Raw output:\n\n{response.text}"
            )
        except Exception as e:
            logger.exception("Error during deep research")
            raise

    def classify_vertical(
        self,
        client_name: str,
        company_overview: str,
    ) -> str:
        """Classify a company into an industry vertical."""
        prompt = self.VERTICAL_CLASSIFICATION_PROMPT.format(
            client_name=client_name,
            company_overview=company_overview,
        )

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )

            vertical = response.text.strip().lower()

            # Validate against known verticals
            valid_verticals = [
                'healthcare', 'finance', 'retail', 'manufacturing', 'technology',
                'energy', 'telecommunications', 'media_entertainment', 'transportation',
                'real_estate', 'professional_services', 'education', 'government',
                'hospitality', 'agriculture', 'construction', 'nonprofit', 'other'
            ]

            if vertical in valid_verticals:
                return vertical
            else:
                logger.warning(f"Unknown vertical returned: {vertical}, defaulting to 'other'")
                return 'other'

        except Exception as e:
            logger.exception("Error during vertical classification")
            return 'other'

    def generate_text(self, prompt: str) -> str:
        """Generate text using Gemini API."""
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            logger.exception("Error generating text")
            raise
