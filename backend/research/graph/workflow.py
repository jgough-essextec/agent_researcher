"""LangGraph workflow definition for the research process."""
from langgraph.graph import StateGraph, END
from .state import ResearchState
from .nodes import (
    validate_input,
    conduct_research,
    classify_vertical,
    search_competitors,
    analyze_gaps,
    finalize_result,
)


def should_continue(state: ResearchState) -> str:
    """Determine if the workflow should continue or end."""
    if state.get('status') == 'failed':
        return 'end'
    return 'continue'


def build_research_workflow():
    """Build and compile the enhanced research workflow graph.

    Workflow stages:
    1. validate - Validate input data and API key
    2. research - Conduct deep research with structured output (AGE-10)
    3. classify - Classify company into industry vertical (AGE-11)
    4. competitors - Search for competitor AI case studies (AGE-12)
    5. gap_analysis - Analyze technology and capability gaps (AGE-13)
    6. finalize - Persist results to database
    """
    # Create the graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node('validate', validate_input)
    workflow.add_node('research', conduct_research)
    workflow.add_node('classify', classify_vertical)
    workflow.add_node('competitors', search_competitors)
    workflow.add_node('gap_analysis', analyze_gaps)
    workflow.add_node('finalize', finalize_result)

    # Set entry point
    workflow.set_entry_point('validate')

    # Add edges with conditional routing
    workflow.add_conditional_edges(
        'validate',
        should_continue,
        {
            'continue': 'research',
            'end': END,
        }
    )

    workflow.add_conditional_edges(
        'research',
        should_continue,
        {
            'continue': 'classify',
            'end': END,
        }
    )

    workflow.add_conditional_edges(
        'classify',
        should_continue,
        {
            'continue': 'competitors',
            'end': END,
        }
    )

    workflow.add_conditional_edges(
        'competitors',
        should_continue,
        {
            'continue': 'gap_analysis',
            'end': END,
        }
    )

    workflow.add_conditional_edges(
        'gap_analysis',
        should_continue,
        {
            'continue': 'finalize',
            'end': END,
        }
    )

    workflow.add_edge('finalize', END)

    # Compile and return
    return workflow.compile()


# Create the compiled workflow
research_workflow = build_research_workflow()
