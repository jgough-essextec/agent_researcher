"""Internal Operations Intelligence service (AGE-20).

Gathers and analyzes public signals about an organization's internal state
to provide sales teams with insight into internal challenges, culture,
and current priorities.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EmployeeSentiment:
    """Employee sentiment data structure."""
    overall_rating: float = 0.0
    work_life_balance: float = 0.0
    compensation: float = 0.0
    culture: float = 0.0
    management: float = 0.0
    recommend_pct: int = 0
    positive_themes: List[str] = field(default_factory=list)
    negative_themes: List[str] = field(default_factory=list)
    trend: str = "stable"  # improving, declining, stable

    def to_dict(self) -> Dict[str, Any]:
        return {
            'overall_rating': self.overall_rating,
            'work_life_balance': self.work_life_balance,
            'compensation': self.compensation,
            'culture': self.culture,
            'management': self.management,
            'recommend_pct': self.recommend_pct,
            'positive_themes': self.positive_themes,
            'negative_themes': self.negative_themes,
            'trend': self.trend,
        }


@dataclass
class LinkedInPresence:
    """LinkedIn presence data structure."""
    follower_count: int = 0
    engagement_level: str = "medium"  # low, medium, high
    recent_posts: List[Dict[str, str]] = field(default_factory=list)  # [{title, summary, date}]
    employee_trend: str = "stable"  # growing, shrinking, stable
    notable_changes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'follower_count': self.follower_count,
            'engagement_level': self.engagement_level,
            'recent_posts': self.recent_posts,
            'employee_trend': self.employee_trend,
            'notable_changes': self.notable_changes,
        }


@dataclass
class SocialMediaMention:
    """Social media mention data structure."""
    platform: str = ""  # reddit, twitter, facebook
    summary: str = ""
    sentiment: str = "neutral"  # positive, negative, neutral, mixed
    topic: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'platform': self.platform,
            'summary': self.summary,
            'sentiment': self.sentiment,
            'topic': self.topic,
        }


@dataclass
class JobPostings:
    """Job postings analysis data structure."""
    total_openings: int = 0
    departments_hiring: Dict[str, int] = field(default_factory=dict)  # {dept_name: count}
    skills_sought: List[str] = field(default_factory=list)
    seniority_distribution: Dict[str, int] = field(default_factory=dict)  # {level: count}
    urgency_signals: List[str] = field(default_factory=list)  # e.g., "signing bonus", "immediate start"
    insights: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_openings': self.total_openings,
            'departments_hiring': self.departments_hiring,
            'skills_sought': self.skills_sought,
            'seniority_distribution': self.seniority_distribution,
            'urgency_signals': self.urgency_signals,
            'insights': self.insights,
        }


@dataclass
class NewsSentiment:
    """News sentiment data structure."""
    overall_sentiment: str = "neutral"  # positive, negative, neutral, mixed
    coverage_volume: str = "low"  # low, medium, high
    topics: List[str] = field(default_factory=list)
    headlines: List[Dict[str, str]] = field(default_factory=list)  # [{title, source, date, sentiment}]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'overall_sentiment': self.overall_sentiment,
            'coverage_volume': self.coverage_volume,
            'topics': self.topics,
            'headlines': self.headlines,
        }


@dataclass
class InternalOpsData:
    """Complete internal operations intelligence data."""
    employee_sentiment: EmployeeSentiment = field(default_factory=EmployeeSentiment)
    linkedin_presence: LinkedInPresence = field(default_factory=LinkedInPresence)
    social_media_mentions: List[SocialMediaMention] = field(default_factory=list)
    job_postings: JobPostings = field(default_factory=JobPostings)
    news_sentiment: NewsSentiment = field(default_factory=NewsSentiment)
    key_insights: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    data_freshness: str = "unknown"
    analysis_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'employee_sentiment': self.employee_sentiment.to_dict(),
            'linkedin_presence': self.linkedin_presence.to_dict(),
            'social_media_mentions': [m.to_dict() for m in self.social_media_mentions],
            'job_postings': self.job_postings.to_dict(),
            'news_sentiment': self.news_sentiment.to_dict(),
            'key_insights': self.key_insights,
            'confidence_score': self.confidence_score,
            'data_freshness': self.data_freshness,
            'analysis_notes': self.analysis_notes,
        }


class InternalOpsService:
    """Service to gather internal operations intelligence."""

    INTERNAL_OPS_PROMPT = '''You are a business intelligence analyst specializing in organizational research. Your task is to analyze publicly available information about a company to gather internal operations intelligence.

Target Company: {client_name}
Industry Vertical: {vertical}
Company Website: {website}
Company Overview: {company_overview}

Research and analyze the following aspects based on publicly available information:

1. EMPLOYEE SENTIMENT (from review sites like Glassdoor, Indeed, Blind)
   - Overall rating and category ratings (work-life balance, compensation, culture, management)
   - Common positive and negative themes from employee reviews
   - Sentiment trend (improving, declining, stable)

2. LINKEDIN PRESENCE
   - Estimated follower count and engagement level
   - Recent company announcements or posts
   - Employee count trends
   - Notable leadership changes or hires

3. SOCIAL MEDIA PRESENCE (Reddit, Twitter/X, Facebook discussions)
   - What are people saying about working at or with this company?
   - Key discussion topics and sentiment

4. JOB POSTINGS ANALYSIS
   - Approximate number of open positions
   - Which departments are hiring most
   - Key skills being sought
   - Seniority levels (entry, mid, senior, executive)
   - Urgency signals (signing bonuses, immediate start, etc.)

5. NEWS SENTIMENT
   - Recent news coverage sentiment
   - Key topics being covered
   - Notable headlines

6. KEY INSIGHTS for sales teams
   - What does this intelligence tell us about the company's current state?
   - What opportunities or challenges does this reveal?

Respond with valid JSON matching this exact structure:
{{
    "employee_sentiment": {{
        "overall_rating": 3.8,
        "work_life_balance": 3.5,
        "compensation": 3.7,
        "culture": 3.6,
        "management": 3.4,
        "recommend_pct": 68,
        "positive_themes": ["Good benefits", "Smart colleagues", "Interesting work"],
        "negative_themes": ["Long hours", "Bureaucracy", "Slow promotions"],
        "trend": "stable"
    }},
    "linkedin_presence": {{
        "follower_count": 50000,
        "engagement_level": "medium",
        "recent_posts": [
            {{"title": "Post title", "summary": "Brief summary", "date": "2024-01"}}
        ],
        "employee_trend": "growing",
        "notable_changes": ["New CTO hired", "Expanded engineering team"]
    }},
    "social_media_mentions": [
        {{
            "platform": "reddit",
            "summary": "Discussion summary on r/tech",
            "sentiment": "mixed",
            "topic": "Work culture"
        }},
        {{
            "platform": "twitter",
            "summary": "Summary of Twitter discussions",
            "sentiment": "neutral",
            "topic": "Product announcements"
        }}
    ],
    "job_postings": {{
        "total_openings": 45,
        "departments_hiring": {{
            "Engineering": 20,
            "Sales": 10,
            "Marketing": 8,
            "Operations": 7
        }},
        "skills_sought": ["Python", "Cloud", "AI/ML", "Leadership"],
        "seniority_distribution": {{
            "Entry": 10,
            "Mid": 20,
            "Senior": 12,
            "Executive": 3
        }},
        "urgency_signals": ["Competitive salary", "Sign-on bonus for engineering roles"],
        "insights": "Heavy focus on technical hiring suggests major development initiative"
    }},
    "news_sentiment": {{
        "overall_sentiment": "positive",
        "coverage_volume": "medium",
        "topics": ["Product launch", "Funding round", "Industry recognition"],
        "headlines": [
            {{"title": "Company Announces New Product", "source": "TechCrunch", "date": "2024-01", "sentiment": "positive"}}
        ]
    }},
    "key_insights": [
        "Heavy engineering hiring suggests major product development underway",
        "Employee reviews indicate culture challenges that may create opportunity for solutions",
        "Recent leadership changes may mean new strategic priorities"
    ],
    "confidence_score": 0.75,
    "data_freshness": "last_30_days",
    "analysis_notes": "Analysis based on publicly available information from LinkedIn, job boards, and news sources."
}}

IMPORTANT:
- Base analysis on what would be publicly available - do not fabricate specific data
- Be realistic with estimates based on company size and industry
- Rate scales: 1.0-5.0 for sentiment ratings, 0-100 for percentages
- confidence_score: 0.0-1.0 based on information availability
- data_freshness options: "last_7_days", "last_30_days", "last_90_days", "older"
- If information is unavailable for a section, use reasonable defaults
- Respond ONLY with valid JSON
'''

    def __init__(self, gemini_client):
        """Initialize with a Gemini client."""
        self.gemini_client = gemini_client

    def research_internal_ops(
        self,
        client_name: str,
        vertical: str = "",
        website: str = "",
        company_overview: str = "",
    ) -> InternalOpsData:
        """Research internal operations intelligence for a company.

        Args:
            client_name: Name of the target company
            vertical: Industry vertical
            website: Company website URL
            company_overview: Brief company description

        Returns:
            InternalOpsData object with gathered intelligence
        """
        prompt = self.INTERNAL_OPS_PROMPT.format(
            client_name=client_name,
            vertical=vertical or "Not specified",
            website=website or "Not available",
            company_overview=company_overview or "Not available",
        )

        try:
            response = self.gemini_client.generate_text(prompt)
            response_text = response.strip()

            # Handle markdown code blocks
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            data = json.loads(response_text)

            # Parse employee sentiment
            es_data = data.get('employee_sentiment', {})
            employee_sentiment = EmployeeSentiment(
                overall_rating=float(es_data.get('overall_rating', 0.0)),
                work_life_balance=float(es_data.get('work_life_balance', 0.0)),
                compensation=float(es_data.get('compensation', 0.0)),
                culture=float(es_data.get('culture', 0.0)),
                management=float(es_data.get('management', 0.0)),
                recommend_pct=int(es_data.get('recommend_pct', 0)),
                positive_themes=es_data.get('positive_themes', []),
                negative_themes=es_data.get('negative_themes', []),
                trend=es_data.get('trend', 'stable'),
            )

            # Parse LinkedIn presence
            li_data = data.get('linkedin_presence', {})
            linkedin_presence = LinkedInPresence(
                follower_count=int(li_data.get('follower_count', 0)),
                engagement_level=li_data.get('engagement_level', 'medium'),
                recent_posts=li_data.get('recent_posts', []),
                employee_trend=li_data.get('employee_trend', 'stable'),
                notable_changes=li_data.get('notable_changes', []),
            )

            # Parse social media mentions
            social_media_mentions = []
            for sm_data in data.get('social_media_mentions', []):
                social_media_mentions.append(SocialMediaMention(
                    platform=sm_data.get('platform', ''),
                    summary=sm_data.get('summary', ''),
                    sentiment=sm_data.get('sentiment', 'neutral'),
                    topic=sm_data.get('topic', ''),
                ))

            # Parse job postings
            jp_data = data.get('job_postings', {})
            job_postings = JobPostings(
                total_openings=int(jp_data.get('total_openings', 0)),
                departments_hiring=jp_data.get('departments_hiring', {}),
                skills_sought=jp_data.get('skills_sought', []),
                seniority_distribution=jp_data.get('seniority_distribution', {}),
                urgency_signals=jp_data.get('urgency_signals', []),
                insights=jp_data.get('insights', ''),
            )

            # Parse news sentiment
            ns_data = data.get('news_sentiment', {})
            news_sentiment = NewsSentiment(
                overall_sentiment=ns_data.get('overall_sentiment', 'neutral'),
                coverage_volume=ns_data.get('coverage_volume', 'low'),
                topics=ns_data.get('topics', []),
                headlines=ns_data.get('headlines', []),
            )

            return InternalOpsData(
                employee_sentiment=employee_sentiment,
                linkedin_presence=linkedin_presence,
                social_media_mentions=social_media_mentions,
                job_postings=job_postings,
                news_sentiment=news_sentiment,
                key_insights=data.get('key_insights', []),
                confidence_score=float(data.get('confidence_score', 0.0)),
                data_freshness=data.get('data_freshness', 'unknown'),
                analysis_notes=data.get('analysis_notes', ''),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse internal ops response: {e}")
            return InternalOpsData(
                analysis_notes=f"Analysis parsing failed: {str(e)}"
            )
        except Exception as e:
            logger.exception("Error during internal ops research")
            return InternalOpsData(
                analysis_notes=f"Research failed: {str(e)}"
            )

    def create_internal_ops_model(
        self,
        research_job,
        ops_data: InternalOpsData,
        gap_correlations: Optional[List[Dict[str, Any]]] = None,
    ):
        """Create InternalOpsIntel model instance.

        Args:
            research_job: The ResearchJob instance
            ops_data: InternalOpsData object
            gap_correlations: Optional list of gap correlation data

        Returns:
            Created InternalOpsIntel instance
        """
        from ..models import InternalOpsIntel

        internal_ops, created = InternalOpsIntel.objects.update_or_create(
            research_job=research_job,
            defaults={
                'employee_sentiment': ops_data.employee_sentiment.to_dict(),
                'linkedin_presence': ops_data.linkedin_presence.to_dict(),
                'social_media_mentions': [m.to_dict() for m in ops_data.social_media_mentions],
                'job_postings': ops_data.job_postings.to_dict(),
                'news_sentiment': ops_data.news_sentiment.to_dict(),
                'key_insights': ops_data.key_insights,
                'gap_correlations': gap_correlations or [],
                'confidence_score': ops_data.confidence_score,
                'data_freshness': ops_data.data_freshness,
                'analysis_notes': ops_data.analysis_notes,
            }
        )

        return internal_ops
