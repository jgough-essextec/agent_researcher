import logging
from django.utils import timezone
from osint.graph.state import OsintState
from osint.models import OsintJob

logger = logging.getLogger(__name__)

PHASE1_PROMPTS = {
    "company_profile": (
        "Research {org} ({domain}). Provide: company history, size, revenue, "
        "leadership team (names, titles), recent news, M&A activity, strategic priorities "
        "from press releases and annual reports. Also identify the industry sector."
    ),
    "breach_history": (
        "Search for any data breaches, cybersecurity incidents, ransomware attacks, "
        "or regulatory enforcement actions involving {org} or the domain {domain}. "
        "Include dates, nature of incident, data exposed, and any fines or settlements."
    ),
    "job_postings": (
        "Search for current and recent job postings from {org}. "
        "Focus on technology and security roles. Identify: technology gaps "
        "(systems they are hiring to implement), security gaps, investment priorities."
    ),
    "vendor_relationships": (
        "Identify technology partnerships, vendor relationships, and tool stack for {org}. "
        "Look for: press releases, case studies, partner program memberships. "
        "Map to: cloud providers, security vendors, infrastructure vendors, SaaS applications."
    ),
    "regulatory_framework": (
        "Identify the regulatory and compliance framework applicable to {org}. "
        "Include: applicable regulations (HIPAA, PCI-DSS, SOX, GDPR, etc.), "
        "certifications they hold or lack, recent regulatory changes that affect them."
    ),
    "leadership_intel": (
        "Research public thought leadership from {org}'s technical and security leadership. "
        "Find: published blogs, conference talks, LinkedIn posts, interviews. "
        "Identify their stated priorities, security philosophy, and known challenges."
    ),
}


def phase1_web_research(state: OsintState) -> OsintState:
    """Phase 1: Web research using Gemini grounded queries."""
    try:
        research_results = _run_web_research(
            org=state['organization_name'],
            domain=state['primary_domain'],
            prior_context=state.get('prior_research_context'),
        )
        OsintJob.objects.filter(pk=state['job_id']).update(
            status='phase1_complete',
            phase1_completed_at=timezone.now(),
        )
        return {
            **state,
            'status': 'phase1_complete',
            'web_research': research_results,
            'error': '',
        }
    except Exception as exc:
        logger.error(
            "phase1_web_research failed for job %s: %s",
            state.get('job_id'),
            exc,
            exc_info=True,
        )
        OsintJob.objects.filter(pk=state['job_id']).update(
            status='failed',
            error=str(exc),
        )
        return {**state, 'status': 'failed', 'error': str(exc), 'web_research': None}


def _run_web_research(org: str, domain: str, prior_context: dict | None) -> dict:
    """Run Gemini grounded queries for Phase 1 OSINT research."""
    from research.services.gemini import GeminiClient
    from research.services.grounding import run_parallel_grounded_queries

    client = GeminiClient()

    prompts = {
        key: template.format(org=org, domain=domain)
        for key, template in PHASE1_PROMPTS.items()
    }

    if prior_context:
        prompts["company_profile"] = (
            f"This is supplemental OSINT security research for {org} ({domain}). "
            f"Prior research context: {str(prior_context)[:500]}. "
            "Focus specifically on: cybersecurity posture, known vulnerabilities, "
            "recent security incidents, and technology gaps."
        )

    grounded_results = run_parallel_grounded_queries(
        genai_client=client.client,
        queries=prompts,
        model=GeminiClient.MODEL_FLASH,
        max_workers=6,
    )

    results: dict = {}
    for key, query_result in grounded_results.items():
        if query_result.success:
            results[key] = {"content": query_result.text, "error": False}
        else:
            results[key] = {
                "content": f"Research for {key} unavailable",
                "error": True,
                "error_detail": query_result.error or "unknown error",
            }

    return results
