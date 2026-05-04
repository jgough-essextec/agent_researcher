import pytest
from osint.graph.workflow import build_osint_workflow, get_graph


def test_workflow_compiles_without_error():
    graph = build_osint_workflow()
    assert graph is not None


def test_get_graph_returns_singleton():
    g1 = get_graph()
    g2 = get_graph()
    assert g1 is g2


def test_workflow_has_expected_nodes():
    graph = build_osint_workflow()
    node_names = set(graph.get_graph().nodes.keys())
    expected = {
        "validate", "phase1_research", "phase2_auto", "generate_commands",
        "phase2_parse", "phase3_screenshots", "phase4_analysis",
        "phase5_report", "finalize"
    }
    assert expected.issubset(node_names)


def test_validate_node_blocks_invalid_domain():
    graph = build_osint_workflow()
    config = {"configurable": {"thread_id": "test-invalid-domain"}}
    state = {
        "job_id": "test", "organization_name": "Acme", "primary_domain": "not_a_domain",
        "additional_domains": [], "engagement_context": "", "research_job_id": None,
        "prior_research_context": None, "status": "pending", "error": "", "warnings": [],
        "web_research": None, "breach_history": None, "job_postings_intel": None,
        "regulatory_framework": None, "vendor_relationships": None, "leadership_intel": None,
        "crt_sh_subdomains": None, "dns_records": None, "email_security": None,
        "whois_data": None, "arin_data": None, "terminal_submissions": None,
        "screenshots": None, "screenshot_analyses": None, "infrastructure_map": None,
        "technology_stack": None, "risk_matrix": None, "severity_table": None,
        "report_sections": None, "service_mappings": None, "report_file_path": None,
    }
    result = graph.invoke(state, config=config)
    assert result["status"] == "failed"
    assert "primary_domain" in result["error"] or "Invalid" in result["error"]
