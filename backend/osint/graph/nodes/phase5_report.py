import json
from django.conf import settings
from osint.graph.state import OsintState
from osint.models import OsintJob, OsintReportSection

SECTION_PROMPTS = {
    'executive_summary': (
        "Write an executive summary for an OSINT security assessment of {org} ({domain}). "
        "Include: organisation overview, key risk findings, overall security posture grade. "
        "Use IBM/Ponemon industry breach cost data to quantify financial risk. "
        "Tone: consultative partner. Use 'observations' not 'vulnerabilities'. "
        "Context: {context}"
    ),
    'remediation_plan': (
        "Create a phased remediation action plan for {org} based on these findings: {severity_table}. "
        "Phase 1 (0-30 days): immediate wins. Phase 2 (30-90 days): infrastructure changes. "
        "Phase 3 (90-180 days): strategic improvements. "
        "Each item: description, owner (IT/Security/Management), effort in hours, cost benchmark."
    ),
    'security_roadmap': (
        "Create a 12-month strategic security roadmap for {org}. "
        "Include specific initiatives, estimated investment, and 3-year vision. "
        "Cover: Zero Trust, unified SOC, TPRM, IR readiness, cloud transformation."
    ),
    'entity_findings': (
        "Write detailed findings for {org} ({domain}). "
        "Include: organisation profile, attack surface inventory ({subdomains_count} subdomains discovered), "
        "email security analysis (SPF: {spf}, DMARC: {dmarc}), "
        "technology stack ({tech_count} vendors identified), regulatory exposure. "
        "All recommendations must be technically specific and actionable."
    ),
    'regulatory_landscape': (
        "Identify and analyse the regulatory compliance landscape for {org}. "
        "Map applicable regulations to OSINT findings: {findings_summary}. "
        "Identify specific compliance gaps revealed by the assessment."
    ),
    'engagement_proposal': (
        "Write a consultative engagement proposal mapping OSINT findings to recommended services. "
        "Service mappings: {service_mappings}. "
        "For each service: scope, duration, deliverables. Framed consultatively as 'how we can help'. "
        "Services: MDR/SOC, Pen Testing/ASM, vCISO/GRC, IR Retainer, "
        "Infrastructure, Digital Workplace, Application Modernization, AI/Intelligent Operations, Field CTO."
    ),
    'methodology': (
        "Write an OSINT methodology appendix for the assessment of {org}. "
        "Describe: passive reconnaissance techniques, certificate transparency queries, "
        "DNS analysis, WHOIS investigation, screenshot-based infrastructure mapping. "
        "Emphasise: all intelligence gathered using passive, legal OSINT only. "
        "No active scanning, no exploitation, no authenticated access."
    ),
}


def phase5_generate_report(state: OsintState) -> OsintState:
    """Phase 5: Generate all report sections via Gemini."""
    try:
        _generate_all_sections(state)
        OsintJob.objects.filter(pk=state['job_id']).update(status='phase5_report')
        return {**state, 'status': 'phase5_report'}
    except Exception as exc:
        OsintJob.objects.filter(pk=state['job_id']).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}


def _generate_all_sections(state: OsintState) -> None:
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    email_sec = state.get('email_security') or {}
    tech_stack = state.get('technology_stack') or []
    severity_table = state.get('severity_table') or []
    service_mappings = state.get('service_mappings') or []

    context_vars = {
        'org': state['organization_name'],
        'domain': state['primary_domain'],
        'context': json.dumps(state.get('web_research') or {})[:1500],
        'severity_table': json.dumps(severity_table[:10])[:1500],
        'subdomains_count': len(state.get('crt_sh_subdomains') or []),
        'spf': email_sec.get('spf_assessment', 'unknown'),
        'dmarc': email_sec.get('dmarc_policy', 'unknown'),
        'tech_count': len(tech_stack),
        'findings_summary': json.dumps(severity_table[:5])[:800],
        'service_mappings': json.dumps(service_mappings[:5])[:1500],
    }

    section_keys = list(SECTION_PROMPTS.keys())
    for i, (section_type, prompt_template) in enumerate(SECTION_PROMPTS.items()):
        try:
            prompt = prompt_template.format(**context_vars)
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            content = response.text.strip()

            OsintReportSection.objects.update_or_create(
                osint_job_id=state['job_id'],
                section_type=section_type,
                defaults={
                    'title': section_type.replace('_', ' ').title(),
                    'content': content,
                    'structured_data': {},
                    'order': i,
                },
            )
        except Exception:
            # Partial failure — write placeholder and continue
            OsintReportSection.objects.update_or_create(
                osint_job_id=state['job_id'],
                section_type=section_type,
                defaults={
                    'title': section_type.replace('_', ' ').title(),
                    'content': f"Section generation failed — manual review required.",
                    'structured_data': {},
                    'order': i,
                },
            )
