"""State definitions for the research workflow."""
from typing import TypedDict, Literal, Optional, Any


class ResearchState(TypedDict):
    """State object for the research workflow."""

    # Input fields
    client_name: str
    sales_history: str
    prompt: str
    job_id: str  # UUID of the ResearchJob

    # Workflow state
    status: Literal['pending', 'researching', 'classifying', 'competitor_search', 'gap_analysis', 'completed', 'failed']

    # Output fields
    result: str
    error: str

    # Structured research output (AGE-10)
    research_report: Optional[dict]

    # Vertical classification (AGE-11)
    vertical: Optional[str]

    # Competitor case studies (AGE-12)
    competitor_case_studies: Optional[list]

    # Gap analysis (AGE-13)
    gap_analysis: Optional[dict]
