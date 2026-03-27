"""LangGraph workflow definition for the research process."""
from langgraph.graph import StateGraph, END
from .state import ResearchState
from .nodes import (
    validate_input,
    conduct_research,
    classify_and_ops,
    search_competitors,
    analyze_gaps,
    correlate_internal_ops,
    finalize_result,
)


def should_continue(state: ResearchState) -> str:
    """Determine if the workflow should continue or end."""
    status = state.get('status')
    if status == 'failed':
        return 'end'
    if status == 'partial':
        return 'finalize'
    return 'continue'


def build_research_workflow():
    """Build and compile the enhanced research workflow graph.

    Workflow stages:
    1. validate     - Validate input data and API key
    2. research     - Conduct deep research with structured output (AGE-10)
    3. classify_and_ops - Classify vertical (AGE-11) + internal ops (AGE-20) in parallel
    4. competitors  - Search for competitor AI case studies (AGE-12)
    5. gap_analysis - Analyze technology and capability gaps (AGE-13)
    6. correlate    - Cross-reference gaps with internal ops evidence (AGE-20)
    7. finalize     - Persist results to database

    classify_and_ops runs both classify and internal_ops concurrently via
    ThreadPoolExecutor, cutting the wall-clock time for that stage roughly in half.
    """
    # Create the graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node('validate', validate_input)
    workflow.add_node('research', conduct_research)
    workflow.add_node('classify_and_ops', classify_and_ops)
    workflow.add_node('competitors', search_competitors)
    workflow.add_node('gap_analysis', analyze_gaps)
    workflow.add_node('correlate', correlate_internal_ops)
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
            'continue': 'classify_and_ops',
            'finalize': 'finalize',
            'end': END,
        }
    )

    workflow.add_conditional_edges(
        'classify_and_ops',
        should_continue,
        {
            'continue': 'competitors',
            'finalize': 'finalize',
            'end': END,
        }
    )

    workflow.add_conditional_edges(
        'competitors',
        should_continue,
        {
            'continue': 'gap_analysis',
            'finalize': 'finalize',
            'end': END,
        }
    )

    workflow.add_conditional_edges(
        'gap_analysis',
        should_continue,
        {
            'continue': 'correlate',
            'finalize': 'finalize',
            'end': END,
        }
    )

    workflow.add_conditional_edges(
        'correlate',
        should_continue,
        {
            'continue': 'finalize',
            'finalize': 'finalize',
            'end': END,
        }
    )

    workflow.add_edge('finalize', END)

    # Compile and return
    return workflow.compile()


# Create the compiled workflow
research_workflow = build_research_workflow()
