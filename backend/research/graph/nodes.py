"""Node functions for the research workflow."""
import logging
from django.conf import settings
from .state import ResearchState

logger = logging.getLogger(__name__)


def validate_input(state: ResearchState) -> ResearchState:
    """Validate the input data before starting research."""
    if not state.get('client_name'):
        return {
            **state,
            'status': 'failed',
            'error': 'Client name is required',
        }

    if not settings.GEMINI_API_KEY:
        return {
            **state,
            'status': 'failed',
            'error': 'Gemini API key is not configured',
        }

    return {
        **state,
        'status': 'researching',
    }


def conduct_research(state: ResearchState) -> ResearchState:
    """Conduct deep research using Gemini API."""
    if state.get('status') == 'failed':
        return state

    try:
        from google import genai

        # Initialize Gemini client
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Format the prompt with client information
        prompt_template = state.get('prompt', '')
        if not prompt_template:
            from prompts.models import PromptTemplate
            prompt_template = PromptTemplate.get_default().content

        formatted_prompt = prompt_template.format(
            client_name=state.get('client_name', ''),
            sales_history=state.get('sales_history', 'No sales history provided'),
        )

        # Use Gemini for research
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=formatted_prompt,
        )

        return {
            **state,
            'status': 'completed',
            'result': response.text,
        }

    except Exception as e:
        logger.exception("Error during research")
        return {
            **state,
            'status': 'failed',
            'error': str(e),
        }


def finalize_result(state: ResearchState) -> ResearchState:
    """Finalize the research result."""
    if state.get('status') == 'failed':
        return state

    return {
        **state,
        'status': 'completed',
    }
