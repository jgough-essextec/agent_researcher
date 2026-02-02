"""LangGraph workflow definition for the research process."""
from langgraph.graph import StateGraph, END
from .state import ResearchState
from .nodes import validate_input, conduct_research, finalize_result


def should_continue(state: ResearchState) -> str:
    """Determine if the workflow should continue or end."""
    if state.get('status') == 'failed':
        return 'end'
    return 'continue'


def build_research_workflow():
    """Build and compile the research workflow graph."""
    # Create the graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node('validate', validate_input)
    workflow.add_node('research', conduct_research)
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
            'continue': 'finalize',
            'end': END,
        }
    )

    workflow.add_edge('finalize', END)

    # Compile and return
    return workflow.compile()


# Create the compiled workflow
research_workflow = build_research_workflow()
