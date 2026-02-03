"""Vertical classification service (AGE-11)."""
import logging
from typing import Optional
from ..constants import Vertical

logger = logging.getLogger(__name__)


class VerticalClassifier:
    """Service to classify companies into industry verticals."""

    # Keyword mappings for quick classification
    KEYWORD_MAPPINGS = {
        Vertical.HEALTHCARE: [
            'hospital', 'health', 'medical', 'pharma', 'biotech', 'healthcare',
            'clinic', 'therapeutic', 'diagnostics', 'patient', 'medicine',
        ],
        Vertical.FINANCE: [
            'bank', 'insurance', 'investment', 'financial', 'fintech', 'capital',
            'asset management', 'wealth', 'trading', 'securities',
        ],
        Vertical.RETAIL: [
            'retail', 'store', 'ecommerce', 'e-commerce', 'consumer', 'shop',
            'marketplace', 'wholesale', 'department store',
        ],
        Vertical.MANUFACTURING: [
            'manufacturing', 'factory', 'industrial', 'production', 'assembly',
            'machinery', 'equipment', 'fabrication',
        ],
        Vertical.TECHNOLOGY: [
            'software', 'saas', 'cloud', 'tech', 'digital', 'platform', 'app',
            'data', 'analytics', 'ai', 'machine learning', 'cybersecurity',
        ],
        Vertical.ENERGY: [
            'energy', 'oil', 'gas', 'utility', 'power', 'renewable', 'solar',
            'wind', 'electric', 'petroleum',
        ],
        Vertical.TELECOMMUNICATIONS: [
            'telecom', 'wireless', 'mobile', 'network', 'broadband', 'internet',
            'cable', 'satellite', '5g', 'communications',
        ],
        Vertical.MEDIA_ENTERTAINMENT: [
            'media', 'entertainment', 'gaming', 'streaming', 'publishing',
            'broadcast', 'film', 'music', 'news', 'advertising',
        ],
        Vertical.TRANSPORTATION: [
            'transport', 'logistics', 'shipping', 'airline', 'automotive',
            'freight', 'delivery', 'trucking', 'rail', 'aviation',
        ],
        Vertical.REAL_ESTATE: [
            'real estate', 'property', 'realty', 'housing', 'commercial property',
            'residential', 'development', 'construction', 'leasing',
        ],
        Vertical.PROFESSIONAL_SERVICES: [
            'consulting', 'advisory', 'legal', 'accounting', 'audit', 'law firm',
            'professional services', 'management consulting',
        ],
        Vertical.EDUCATION: [
            'education', 'university', 'school', 'learning', 'training',
            'academic', 'edtech', 'college', 'curriculum',
        ],
        Vertical.GOVERNMENT: [
            'government', 'federal', 'state', 'municipal', 'public sector',
            'agency', 'defense', 'military',
        ],
        Vertical.HOSPITALITY: [
            'hotel', 'hospitality', 'restaurant', 'travel', 'tourism',
            'resort', 'lodging', 'food service', 'cruise',
        ],
        Vertical.AGRICULTURE: [
            'agriculture', 'farming', 'agri', 'crop', 'livestock', 'food',
            'agtech', 'agricultural',
        ],
        Vertical.CONSTRUCTION: [
            'construction', 'building', 'engineering', 'infrastructure',
            'contractor', 'architecture',
        ],
        Vertical.NONPROFIT: [
            'nonprofit', 'non-profit', 'charity', 'foundation', 'ngo',
            'association', 'organization',
        ],
    }

    def __init__(self, gemini_client=None):
        """Initialize the classifier with an optional Gemini client."""
        self.gemini_client = gemini_client

    def classify(
        self,
        client_name: str,
        company_overview: str = "",
        use_llm: bool = True,
    ) -> str:
        """Classify a company into an industry vertical.

        Args:
            client_name: Name of the company
            company_overview: Description of the company
            use_llm: Whether to use LLM for classification (falls back to keyword matching)

        Returns:
            Vertical string value
        """
        # First, try keyword-based classification for speed
        keyword_result = self._classify_by_keywords(client_name, company_overview)

        if keyword_result and not use_llm:
            return keyword_result

        # Use LLM for more accurate classification
        if use_llm and self.gemini_client:
            try:
                llm_result = self.gemini_client.classify_vertical(
                    client_name=client_name,
                    company_overview=company_overview,
                )
                return llm_result
            except Exception as e:
                logger.warning(f"LLM classification failed, using keyword result: {e}")
                return keyword_result or Vertical.OTHER.value

        return keyword_result or Vertical.OTHER.value

    def _classify_by_keywords(
        self,
        client_name: str,
        company_overview: str,
    ) -> Optional[str]:
        """Classify using keyword matching."""
        text = f"{client_name} {company_overview}".lower()

        scores = {}
        for vertical, keywords in self.KEYWORD_MAPPINGS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[vertical] = score

        if scores:
            best_vertical = max(scores, key=scores.get)
            return best_vertical.value

        return None
