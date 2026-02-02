"""State definitions for the research workflow."""
from typing import TypedDict, Literal


class ResearchState(TypedDict):
    """State object for the research workflow."""

    # Input fields
    client_name: str
    sales_history: str
    prompt: str

    # Workflow state
    status: Literal['pending', 'researching', 'completed', 'failed']

    # Output fields
    result: str
    error: str
