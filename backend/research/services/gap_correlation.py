"""Gap Correlation Service (AGE-20).

Cross-references Gap Analysis findings with Internal Operations Intelligence
to provide evidence-backed insights for sales teams.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GapCorrelation:
    """Data structure for a gap correlation."""
    gap_type: str = ""  # technology, capability, process
    description: str = ""
    evidence: str = ""
    evidence_type: str = "supporting"  # supporting, contradicting, neutral
    confidence: float = 0.0
    sales_implication: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'gap_type': self.gap_type,
            'description': self.description,
            'evidence': self.evidence,
            'evidence_type': self.evidence_type,
            'confidence': self.confidence,
            'sales_implication': self.sales_implication,
        }


class GapCorrelationService:
    """Service to correlate gaps with internal ops evidence."""

    GAP_CORRELATION_PROMPT = '''You are a sales intelligence analyst. Your task is to cross-reference identified gaps in a target company with internal operations intelligence to provide evidence-backed insights.

Target Company: {client_name}
Industry Vertical: {vertical}

## IDENTIFIED GAPS

### Technology Gaps:
{technology_gaps}

### Capability Gaps:
{capability_gaps}

### Process Gaps:
{process_gaps}

## INTERNAL OPERATIONS INTELLIGENCE

### Employee Sentiment:
Overall Rating: {employee_rating}/5.0
Trend: {employee_trend}
Positive Themes: {positive_themes}
Negative Themes: {negative_themes}

### Job Postings:
Total Openings: {total_openings}
Key Departments Hiring: {departments_hiring}
Skills Sought: {skills_sought}
Urgency Signals: {urgency_signals}
Hiring Insights: {job_insights}

### News & Social Sentiment:
News Sentiment: {news_sentiment}
Key Topics: {news_topics}

### Key Internal Insights:
{key_insights}

## YOUR TASK

For each identified gap, analyze the internal ops intelligence to find:
1. Supporting evidence - signals that confirm or reinforce the gap
2. Contradicting evidence - signals that suggest the gap may not exist or is being addressed
3. Sales implications - how to use this information in sales conversations

Respond with valid JSON matching this structure:
{{
    "gap_correlations": [
        {{
            "gap_type": "technology",
            "description": "The specific gap being analyzed",
            "evidence": "Internal ops evidence that relates to this gap",
            "evidence_type": "supporting",
            "confidence": 0.85,
            "sales_implication": "How to leverage this in sales conversations"
        }},
        {{
            "gap_type": "capability",
            "description": "Another gap",
            "evidence": "Related evidence from job postings or reviews",
            "evidence_type": "supporting",
            "confidence": 0.70,
            "sales_implication": "Sales approach recommendation"
        }}
    ],
    "overall_confidence": 0.75,
    "analysis_summary": "Brief summary of the correlation analysis"
}}

IMPORTANT:
- Analyze EACH gap from all three categories (technology, capability, process)
- evidence_type must be: "supporting", "contradicting", or "neutral"
- confidence should be 0.0-1.0 based on how strong the correlation is
- Focus on actionable sales implications
- If no clear evidence exists for a gap, note it with confidence of 0.3 or less
- Respond ONLY with valid JSON
'''

    def __init__(self, gemini_client):
        """Initialize with a Gemini client."""
        self.gemini_client = gemini_client

    def correlate_gaps(
        self,
        client_name: str,
        vertical: str,
        gap_analysis: Dict[str, Any],
        internal_ops: Dict[str, Any],
    ) -> List[GapCorrelation]:
        """Correlate gaps with internal ops evidence.

        Args:
            client_name: Name of the target company
            vertical: Industry vertical
            gap_analysis: Gap analysis data dictionary
            internal_ops: Internal ops intelligence data dictionary

        Returns:
            List of GapCorrelation objects
        """
        # Extract gap data
        technology_gaps = gap_analysis.get('technology_gaps', [])
        capability_gaps = gap_analysis.get('capability_gaps', [])
        process_gaps = gap_analysis.get('process_gaps', [])

        # Extract internal ops data
        employee_sentiment = internal_ops.get('employee_sentiment', {})
        job_postings = internal_ops.get('job_postings', {})
        news_sentiment = internal_ops.get('news_sentiment', {})
        key_insights = internal_ops.get('key_insights', [])

        prompt = self.GAP_CORRELATION_PROMPT.format(
            client_name=client_name,
            vertical=vertical or "Not specified",
            technology_gaps='\n'.join(f"- {g}" for g in technology_gaps) or "None identified",
            capability_gaps='\n'.join(f"- {g}" for g in capability_gaps) or "None identified",
            process_gaps='\n'.join(f"- {g}" for g in process_gaps) or "None identified",
            employee_rating=employee_sentiment.get('overall_rating', 'N/A'),
            employee_trend=employee_sentiment.get('trend', 'Unknown'),
            positive_themes=', '.join(employee_sentiment.get('positive_themes', [])) or 'None noted',
            negative_themes=', '.join(employee_sentiment.get('negative_themes', [])) or 'None noted',
            total_openings=job_postings.get('total_openings', 0),
            departments_hiring=json.dumps(job_postings.get('departments_hiring', {})),
            skills_sought=', '.join(job_postings.get('skills_sought', [])) or 'None noted',
            urgency_signals=', '.join(job_postings.get('urgency_signals', [])) or 'None noted',
            job_insights=job_postings.get('insights', 'Not available'),
            news_sentiment=news_sentiment.get('overall_sentiment', 'Unknown'),
            news_topics=', '.join(news_sentiment.get('topics', [])) or 'None noted',
            key_insights='\n'.join(f"- {i}" for i in key_insights) or "None available",
        )

        try:
            response = self.gemini_client.generate_text(prompt)
            response_text = response.strip()

            # Handle markdown code blocks
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            data = json.loads(response_text)

            correlations = []
            for corr_data in data.get('gap_correlations', []):
                correlations.append(GapCorrelation(
                    gap_type=corr_data.get('gap_type', ''),
                    description=corr_data.get('description', ''),
                    evidence=corr_data.get('evidence', ''),
                    evidence_type=corr_data.get('evidence_type', 'neutral'),
                    confidence=float(corr_data.get('confidence', 0.0)),
                    sales_implication=corr_data.get('sales_implication', ''),
                ))

            return correlations

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse gap correlation response: {e}")
            return []
        except Exception as e:
            logger.exception("Error during gap correlation")
            return []

    def correlations_to_dict(self, correlations: List[GapCorrelation]) -> List[Dict[str, Any]]:
        """Convert list of GapCorrelation objects to list of dictionaries."""
        return [c.to_dict() for c in correlations]
