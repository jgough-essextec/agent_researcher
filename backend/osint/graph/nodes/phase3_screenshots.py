import logging

from osint.graph.state import OsintState
from osint.models import OsintJob, ScreenshotUpload

logger = logging.getLogger(__name__)


def phase3_analyze_screenshots(state: OsintState) -> OsintState:
    """Phase 3: Analyze user-uploaded screenshots via Gemini vision."""
    screenshot_ids = state.get('screenshots') or []

    if not screenshot_ids:
        OsintJob.objects.filter(pk=state['job_id']).update(status='phase4_analysis')
        return {**state, 'status': 'phase4_analysis', 'screenshot_analyses': []}

    try:
        analyses = _analyze_all_screenshots(screenshot_ids, state['primary_domain'])
        _save_analyses_to_db(screenshot_ids, analyses)
        OsintJob.objects.filter(pk=state['job_id']).update(status='phase4_analysis')
        return {**state, 'status': 'phase4_analysis', 'screenshot_analyses': analyses}
    except Exception as exc:
        logger.error("Phase 3 screenshot analysis failed for job %s: %s", state['job_id'], exc)
        OsintJob.objects.filter(pk=state['job_id']).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}


def _analyze_all_screenshots(screenshot_ids: list, domain: str) -> list[dict]:
    from osint.services.screenshot_analyzer import analyze_screenshot

    analyses = []
    for sid in screenshot_ids:
        try:
            screenshot = ScreenshotUpload.objects.get(pk=sid)
            image_bytes = screenshot.image.read()
            result = analyze_screenshot(image_bytes, source=screenshot.source, domain=domain)
            analyses.append({
                'screenshot_id': str(sid),
                'source': screenshot.source,
                'hosts_and_ips': list(result.hosts_and_ips),
                'technology_indicators': list(result.technology_indicators),
                'security_observations': list(result.security_observations),
                'infrastructure_providers': list(result.infrastructure_providers),
                'notable_findings': list(result.notable_findings),
                'error': result.error,
            })
        except Exception as exc:
            logger.warning("Failed to analyze screenshot %s: %s", sid, exc)
            analyses.append({'screenshot_id': str(sid), 'error': str(exc)})
    return analyses


def _save_analyses_to_db(screenshot_ids: list, analyses: list[dict]) -> None:
    for analysis in analyses:
        sid = analysis.get('screenshot_id')
        if sid:
            ScreenshotUpload.objects.filter(pk=sid).update(
                analysis=str(analysis)[:5000],
                extracted_data={k: v for k, v in analysis.items() if k != 'screenshot_id'},
            )
