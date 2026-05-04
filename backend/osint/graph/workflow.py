import threading
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import OsintState
from .nodes.validate import validate_osint_input
from .nodes.phase1_research import phase1_web_research
from .nodes.phase2_auto_dns import phase2_auto_dns
from .nodes.phase2_commands import generate_terminal_commands
from .nodes.phase2_parse import phase2_parse_terminal
from .nodes.phase3_screenshots import phase3_analyze_screenshots
from .nodes.phase4_analysis import phase4_analysis
from .nodes.phase5_report import phase5_generate_report
from .nodes.finalize import finalize_osint

_workflow_lock = threading.Lock()
_compiled_graph = None


def _should_continue(state: OsintState) -> str:
    return "end" if state.get("status") == "failed" else "continue"


def build_osint_workflow():
    """Build and compile the OSINT LangGraph workflow with interrupt support."""
    workflow = StateGraph(OsintState)

    workflow.add_node("validate", validate_osint_input)
    workflow.add_node("phase1_research", phase1_web_research)
    workflow.add_node("phase2_auto", phase2_auto_dns)
    workflow.add_node("generate_commands", generate_terminal_commands)
    workflow.add_node("phase2_parse", phase2_parse_terminal)
    workflow.add_node("phase3_screenshots", phase3_analyze_screenshots)
    workflow.add_node("phase4_analysis", phase4_analysis)
    workflow.add_node("phase5_report", phase5_generate_report)
    workflow.add_node("finalize", finalize_osint)

    workflow.set_entry_point("validate")
    workflow.add_conditional_edges(
        "validate", _should_continue, {"continue": "phase1_research", "end": END}
    )
    workflow.add_edge("phase1_research", "phase2_auto")
    workflow.add_edge("phase2_auto", "generate_commands")
    workflow.add_edge("generate_commands", "phase2_parse")
    workflow.add_edge("phase2_parse", "phase3_screenshots")
    workflow.add_edge("phase3_screenshots", "phase4_analysis")
    workflow.add_edge("phase4_analysis", "phase5_report")
    workflow.add_edge("phase5_report", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_after=["generate_commands"],
        interrupt_before=["phase3_screenshots"],
    )


def get_graph():
    """Return the singleton compiled graph (thread-safe lazy init)."""
    global _compiled_graph
    if _compiled_graph is None:
        with _workflow_lock:
            if _compiled_graph is None:
                _compiled_graph = build_osint_workflow()
    return _compiled_graph
