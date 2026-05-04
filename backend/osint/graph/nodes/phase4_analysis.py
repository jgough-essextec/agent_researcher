import json
from django.conf import settings
from django.utils import timezone
from osint.graph.state import OsintState
from osint.models import OsintJob, InfrastructureFinding, ServiceMapping

SYNTHESIS_PROMPT = """You are a world-class cybersecurity analyst. Synthesise the following OSINT findings for {org} ({domain}).

EMAIL SECURITY: DMARC policy={dmarc_policy}, SPF={spf_assessment}, Email grade={email_grade}
SUBDOMAINS FOUND: {subdomains_count}
TECHNOLOGY INDICATORS: {tech_signals}
SCREENSHOT OBSERVATIONS: {screenshot_obs}
WEB RESEARCH SUMMARY: {web_summary}

Produce a structured JSON assessment:
{{
    "infrastructure_map": {{
        "cloud_providers": ["string"],
        "cdn_providers": ["string"],
        "email_providers": ["string"],
        "dns_providers": ["string"]
    }},
    "technology_stack": [
        {{
            "vendor": "string",
            "product": "string",
            "category": "Email|Identity|Security|Infrastructure|Cloud|Endpoint|Network",
            "evidence": ["source"],
            "confidence": "high|medium|low",
            "pellera_service_relevance": ["mdr_soc|pen_test|vciso_grc|ir_retainer|infrastructure|digital_workplace|app_modernization|ai_ops|field_cto"]
        }}
    ],
    "risk_matrix": [
        {{
            "finding": "string",
            "description": "string",
            "likelihood": 3,
            "impact": 3,
            "remediation_phase": 1
        }}
    ],
    "severity_table": [
        {{
            "finding": "string",
            "severity": "critical|high|medium|low|info",
            "category": "string",
            "remediation_action": "string"
        }}
    ],
    "service_mappings": [
        {{
            "service": "mdr_soc|pen_test|vciso_grc|ir_retainer|infrastructure|digital_workplace|app_modernization|ai_ops|field_cto",
            "finding_summary": "string",
            "urgency": "immediate|short_term|strategic",
            "justification": "string"
        }}
    ]
}}

Return ONLY valid JSON."""


def phase4_analysis(state: OsintState) -> OsintState:
    """Phase 4: Synthesise all findings into infrastructure map, risk matrix, service mappings."""
    try:
        synthesis = _run_synthesis(state)
        _persist_synthesis(state['job_id'], synthesis)
        OsintJob.objects.filter(pk=state['job_id']).update(
            status='phase4_analysis',
            phase4_completed_at=timezone.now(),
        )
        return {
            **state,
            'status': 'phase4_analysis',
            'infrastructure_map': synthesis.get('infrastructure_map'),
            'technology_stack': synthesis.get('technology_stack'),
            'risk_matrix': synthesis.get('risk_matrix'),
            'severity_table': synthesis.get('severity_table'),
            'service_mappings': synthesis.get('service_mappings'),
            'error': '',
        }
    except Exception as exc:
        OsintJob.objects.filter(pk=state['job_id']).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}


def _run_synthesis(state: OsintState) -> dict:
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    email_sec = state.get('email_security') or {}
    terminal_subs = state.get('terminal_submissions') or []
    screenshot_analyses = state.get('screenshot_analyses') or []

    tech_signals = []
    for sub in terminal_subs:
        tech_signals.extend(sub.get('technology_signals', []))
    for analysis in screenshot_analyses:
        tech_signals.extend(analysis.get('technology_indicators', []))

    screenshot_obs = []
    for analysis in screenshot_analyses:
        screenshot_obs.extend(analysis.get('security_observations', []))

    prompt = SYNTHESIS_PROMPT.format(
        org=state['organization_name'],
        domain=state['primary_domain'],
        dmarc_policy=email_sec.get('dmarc_policy', 'unknown'),
        spf_assessment=email_sec.get('spf_assessment', 'unknown'),
        email_grade=email_sec.get('overall_grade', 'unknown'),
        subdomains_count=len(state.get('crt_sh_subdomains') or []),
        tech_signals=json.dumps(tech_signals[:20])[:500],
        screenshot_obs=json.dumps(screenshot_obs[:10])[:500],
        web_summary=json.dumps(state.get('web_research') or {})[:1000],
    )

    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    text = response.text.strip()
    if text.startswith("```"):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1] if lines and lines[-1].strip() == '```' else lines[1:])
    return json.loads(text)


def _persist_synthesis(job_id: str, synthesis: dict) -> None:
    infra = synthesis.get('infrastructure_map', {})
    for provider in infra.get('cloud_providers', []):
        InfrastructureFinding.objects.create(
            osint_job_id=job_id,
            infra_type='cloud_provider',
            provider_name=provider,
            evidence='AI synthesis from Phase 1-3 findings',
            confidence=0.8,
        )
    for mapping in synthesis.get('service_mappings', []):
        service_val = mapping.get('service', 'field_cto')
        valid_services = {
            'mdr_soc', 'pen_test', 'vciso_grc', 'ir_retainer', 'infrastructure',
            'digital_workplace', 'app_modernization', 'ai_ops', 'field_cto',
        }
        if service_val not in valid_services:
            service_val = 'field_cto'
        ServiceMapping.objects.create(
            osint_job_id=job_id,
            service=service_val,
            finding_summary=mapping.get('finding_summary', '')[:500],
            urgency=mapping.get('urgency', 'strategic'),
            justification=mapping.get('justification', '')[:1000],
        )
