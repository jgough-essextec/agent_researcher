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


def run_from_terminal_submission(job_id: str, submissions: list) -> None:
    """Resume pipeline from Phase 2 parse using DB state — safe across Cloud Run instances.

    MemorySaver checkpoints are in-process memory. Cloud Run can route resume
    requests to a different instance where the checkpoint no longer exists.
    This function bypasses the checkpoint by rebuilding state from the DB and
    invoking the remaining nodes directly.
    """
    from osint.models import OsintJob, DnsFinding, SubdomainFinding, EmailSecurityAssessment, WhoisRecord

    try:
        job = OsintJob.objects.get(pk=job_id)

        # Rebuild state from DB records written during Phase 1 and Phase 2 auto
        dns_records = [
            {"domain": f.domain, "record_type": f.record_type, "values": [f.record_value]}
            for f in DnsFinding.objects.filter(osint_job=job)
        ]
        subdomains = [
            {"name_value": s.subdomain, "issuer_name": ""}
            for s in SubdomainFinding.objects.filter(osint_job=job)
        ]
        email_assessment = EmailSecurityAssessment.objects.filter(osint_job=job).first()
        whois = WhoisRecord.objects.filter(osint_job=job).first()

        state = {
            "job_id": job_id,
            "organization_name": job.organization_name,
            "primary_domain": job.primary_domain,
            "additional_domains": list(job.additional_domains),
            "engagement_context": job.engagement_context,
            "research_job_id": str(job.research_job_id) if job.research_job_id else None,
            "prior_research_context": None,
            "status": "phase2_processing",
            "error": "",
            "warnings": [],
            "web_research": None,
            "breach_history": None,
            "job_postings_intel": None,
            "regulatory_framework": None,
            "vendor_relationships": None,
            "leadership_intel": None,
            "crt_sh_subdomains": subdomains,
            "dns_records": dns_records,
            "email_security": {
                "domain": email_assessment.domain,
                "has_spf": email_assessment.has_spf,
                "spf_assessment": email_assessment.spf_assessment,
                "has_dmarc": email_assessment.has_dmarc,
                "dmarc_policy": email_assessment.dmarc_policy,
                "overall_grade": email_assessment.overall_grade,
                "risk_summary": email_assessment.risk_summary,
                "mx_providers": email_assessment.mx_providers,
            } if email_assessment else None,
            "whois_data": {
                "registrant_org": whois.registrant_org,
                "registrar": whois.registrar,
                "name_servers": whois.name_servers,
            } if whois else None,
            "arin_data": None,
            "terminal_submissions": submissions,
            "screenshots": None,
            "screenshot_analyses": None,
            "infrastructure_map": None,
            "technology_stack": None,
            "risk_matrix": None,
            "severity_table": None,
            "report_sections": None,
            "service_mappings": None,
            "report_file_path": None,
        }

        # Run remaining nodes directly — no checkpoint dependency
        state = phase2_parse_terminal(state)
        if state.get("status") == "failed":
            return
        # phase2_parse sets status to awaiting_screenshots — stop here and wait for user
    except Exception as exc:
        from osint.models import OsintJob as _OJ
        _OJ.objects.filter(pk=job_id).update(status="failed", error=str(exc))


def run_from_screenshots(job_id: str, screenshot_ids: list) -> None:
    """Resume pipeline from Phase 3 screenshots using DB state — safe across Cloud Run instances."""
    from osint.models import OsintJob, DnsFinding, SubdomainFinding, EmailSecurityAssessment, WhoisRecord, TerminalSubmission

    try:
        job = OsintJob.objects.get(pk=job_id)

        dns_records = [
            {"domain": f.domain, "record_type": f.record_type, "values": [f.record_value]}
            for f in DnsFinding.objects.filter(osint_job=job)
        ]
        subdomains = [
            {"name_value": s.subdomain, "issuer_name": ""}
            for s in SubdomainFinding.objects.filter(osint_job=job)
        ]
        email_assessment = EmailSecurityAssessment.objects.filter(osint_job=job).first()
        terminal_subs = [
            {"technology_signals": list(ts.parsed_data.get("technology_signals", []))}
            for ts in TerminalSubmission.objects.filter(osint_job=job)
        ]

        state = {
            "job_id": job_id,
            "organization_name": job.organization_name,
            "primary_domain": job.primary_domain,
            "additional_domains": list(job.additional_domains),
            "engagement_context": job.engagement_context,
            "research_job_id": str(job.research_job_id) if job.research_job_id else None,
            "prior_research_context": None,
            "status": "phase3_processing",
            "error": "",
            "warnings": [],
            "web_research": None,
            "breach_history": None,
            "job_postings_intel": None,
            "regulatory_framework": None,
            "vendor_relationships": None,
            "leadership_intel": None,
            "crt_sh_subdomains": subdomains,
            "dns_records": dns_records,
            "email_security": {
                "domain": email_assessment.domain,
                "has_spf": email_assessment.has_spf,
                "spf_assessment": email_assessment.spf_assessment,
                "has_dmarc": email_assessment.has_dmarc,
                "dmarc_policy": email_assessment.dmarc_policy,
                "overall_grade": email_assessment.overall_grade,
                "risk_summary": email_assessment.risk_summary,
                "mx_providers": email_assessment.mx_providers,
            } if email_assessment else None,
            "whois_data": None,
            "arin_data": None,
            "terminal_submissions": terminal_subs,
            "screenshots": screenshot_ids,
            "screenshot_analyses": None,
            "infrastructure_map": None,
            "technology_stack": None,
            "risk_matrix": None,
            "severity_table": None,
            "report_sections": None,
            "service_mappings": None,
            "report_file_path": None,
        }

        # Run remaining nodes directly — no checkpoint dependency
        state = phase3_analyze_screenshots(state)
        if state.get("status") == "failed":
            return
        state = phase4_analysis(state)
        if state.get("status") == "failed":
            return
        state = phase5_generate_report(state)
        if state.get("status") == "failed":
            return
        finalize_osint(state)
    except Exception as exc:
        from osint.models import OsintJob as _OJ
        _OJ.objects.filter(pk=job_id).update(status="failed", error=str(exc))
