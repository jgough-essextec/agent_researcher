"""Node functions for the research workflow."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from django.db import transaction
from .state import ResearchState

logger = logging.getLogger(__name__)


def _update_job_step(job_id: str, step: str) -> None:
    """Write current_step to DB so frontend polling can show progress. Non-fatal."""
    if not job_id:
        return
    try:
        from ..models import ResearchJob
        ResearchJob.objects.filter(id=job_id).update(current_step=step)
    except Exception:
        pass


def validate_input(state: ResearchState) -> ResearchState:
    """Validate the input data before starting research."""
    if not state.get('client_name'):
        return {
            **state,
            'status': 'failed',
            'error': 'Client name is required',
        }

    if not settings.GEMINI_API_KEY:
        return {
            **state,
            'status': 'failed',
            'error': 'Gemini API key is not configured',
        }

    return {
        **state,
        'status': 'researching',
    }


def conduct_research(state: ResearchState) -> ResearchState:
    """Conduct deep research using Gemini API with Google Search grounding (AGE-10)."""
    if state.get('status') == 'failed':
        return state

    _update_job_step(state.get('job_id'), 'research')

    try:
        from ..services.gemini import GeminiClient

        client = GeminiClient()

        # Conduct structured deep research with grounding
        report_data, grounding_metadata, synthesis_text = client.conduct_deep_research(
            client_name=state.get('client_name', ''),
            sales_history=state.get('sales_history', ''),
            prompt=state.get('prompt', ''),
        )

        # Convert to dict for state storage
        report_dict = report_data.to_dict()

        # Extract web sources from grounding metadata
        web_sources = []
        if grounding_metadata:
            web_sources = grounding_metadata.to_dict().get('web_sources', [])

        # Validation gate: if fewer than 5 meaningful fields populated, treat as partial
        meaningful_fields = [
            report_dict.get('company_overview'),
            report_dict.get('headquarters'),
            report_dict.get('employee_count'),
            report_dict.get('annual_revenue'),
            report_dict.get('ai_footprint'),
            report_dict.get('cloud_footprint'),
            report_dict.get('digital_maturity'),
            report_dict.get('strategic_goals'),
            report_dict.get('key_initiatives'),
        ]
        populated = sum(1 for f in meaningful_fields if f)
        if populated < 5:
            logger.warning(
                f"Research for '{state.get('client_name')}' yielded only {populated}/9 fields — "
                "routing to partial status"
            )
            return {
                **state,
                'status': 'partial',
                'synthesis_text': synthesis_text,
                'web_sources': web_sources,
                'warnings': (state.get('warnings') or []) + [
                    f'JSON parsing yielded only {populated}/9 structured fields. Raw synthesis preserved.'
                ],
            }

        # Also generate plain text result for backward compatibility
        result_text = _format_research_result(report_dict)

        return {
            **state,
            'status': 'classifying',
            'result': result_text,
            'research_report': report_dict,
            'synthesis_text': synthesis_text,
            'web_sources': web_sources,
        }

    except Exception as e:
        logger.exception("Error during research")
        return {
            **state,
            'status': 'failed',
            'error': str(e),
        }


def classify_vertical(state: ResearchState) -> ResearchState:
    """Classify the company into an industry vertical (AGE-11)."""
    if state.get('status') in ('failed', 'partial'):
        return state

    _update_job_step(state.get('job_id'), 'classify')

    try:
        from ..services.gemini import GeminiClient
        from ..services.classifier import VerticalClassifier

        gemini_client = GeminiClient()
        classifier = VerticalClassifier(gemini_client=gemini_client)

        report = state.get('research_report', {})
        vertical = classifier.classify(
            client_name=state.get('client_name', ''),
            company_overview=report.get('company_overview', ''),
            use_llm=True,
        )

        return {
            **state,
            'status': 'competitor_search',
            'vertical': vertical,
        }

    except Exception as e:
        logger.exception("Error during vertical classification")
        # Non-fatal, continue with 'other' vertical
        return {
            **state,
            'status': 'competitor_search',
            'vertical': 'other',
        }


def search_competitors(state: ResearchState) -> ResearchState:
    """Search for competitor AI case studies (AGE-12)."""
    if state.get('status') in ('failed', 'partial'):
        return state

    _update_job_step(state.get('job_id'), 'competitors')

    try:
        from ..services.gemini import GeminiClient
        from ..services.competitor import CompetitorSearchService

        gemini_client = GeminiClient()
        competitor_service = CompetitorSearchService(gemini_client)

        report = state.get('research_report', {})
        case_studies, comp_metadata = competitor_service.search_competitor_case_studies(
            client_name=state.get('client_name', ''),
            vertical=state.get('vertical', 'other'),
            company_overview=report.get('company_overview', ''),
        )

        # Convert to list of dicts for state storage
        case_studies_list = [
            {
                'competitor_name': cs.competitor_name,
                'vertical': cs.vertical,
                'case_study_title': cs.case_study_title,
                'summary': cs.summary,
                'technologies_used': cs.technologies_used,
                'outcomes': cs.outcomes,
                'source_url': cs.source_url,
                'relevance_score': cs.relevance_score,
            }
            for cs in case_studies
        ]

        # Accumulate grounding sources
        existing_sources = state.get('web_sources', [])
        if comp_metadata:
            comp_sources = comp_metadata.to_dict().get('web_sources', [])
            merged_sources = existing_sources + [s for s in comp_sources if s not in existing_sources]
        else:
            merged_sources = existing_sources

        return {
            **state,
            'status': 'gap_analysis',
            'competitor_case_studies': case_studies_list,
            'web_sources': merged_sources,
        }

    except Exception as e:
        logger.exception("Error during competitor search")
        # Non-fatal, continue without competitor data — surface failure in warnings
        return {
            **state,
            'status': 'gap_analysis',
            'competitor_case_studies': [],
            'warnings': (state.get('warnings') or []) + [
                f'Competitor search failed: {str(e)}'
            ],
        }


def analyze_gaps(state: ResearchState) -> ResearchState:
    """Analyze technology and capability gaps (AGE-13)."""
    if state.get('status') in ('failed', 'partial'):
        return state

    _update_job_step(state.get('job_id'), 'gap_analysis')

    try:
        from ..services.gemini import GeminiClient
        from ..services.gap_analysis import GapAnalysisService

        gemini_client = GeminiClient()
        gap_service = GapAnalysisService(gemini_client)

        report = state.get('research_report', {})
        gap_data = gap_service.analyze_gaps(
            client_name=state.get('client_name', ''),
            vertical=state.get('vertical', 'other'),
            company_overview=report.get('company_overview', ''),
            sales_history=state.get('sales_history', ''),
            prompt=state.get('prompt', ''),
            pain_points=report.get('pain_points', []),
            opportunities=report.get('opportunities', []),
            strategic_goals=report.get('strategic_goals', []),
            key_initiatives=report.get('key_initiatives', []),
            digital_maturity=report.get('digital_maturity', ''),
            ai_footprint=report.get('ai_footprint', ''),
            ai_adoption_stage=report.get('ai_adoption_stage', ''),
            competitor_case_studies=state.get('competitor_case_studies', []),
        )

        # Convert to dict for state storage
        gap_dict = {
            'technology_gaps': gap_data.technology_gaps,
            'capability_gaps': gap_data.capability_gaps,
            'process_gaps': gap_data.process_gaps,
            'recommendations': gap_data.recommendations,
            'priority_areas': gap_data.priority_areas,
            'confidence_score': gap_data.confidence_score,
            'analysis_notes': gap_data.analysis_notes,
        }

        return {
            **state,
            'status': 'completed',
            'gap_analysis': gap_dict,
        }

    except Exception as e:
        logger.exception("Error during gap analysis")
        # Non-fatal, continue without gap analysis
        return {
            **state,
            'status': 'completed',
            'gap_analysis': None,
        }


def research_internal_ops(state: ResearchState) -> ResearchState:
    """Research internal operations intelligence (AGE-20).

    This runs in parallel with the main research pipeline.
    Gathers employee sentiment, LinkedIn presence, job postings, etc.
    """
    if state.get('status') in ('failed', 'partial'):
        return state

    _update_job_step(state.get('job_id'), 'internal_ops')

    try:
        from ..services.gemini import GeminiClient
        from ..services.internal_ops import InternalOpsService

        gemini_client = GeminiClient()
        internal_ops_service = InternalOpsService(gemini_client)

        report = state.get('research_report', {})
        ops_data, ops_metadata = internal_ops_service.research_internal_ops(
            client_name=state.get('client_name', ''),
            vertical=state.get('vertical', ''),
            website=report.get('website', ''),
            company_overview=report.get('company_overview', ''),
        )

        # Convert to dict for state storage
        ops_dict = ops_data.to_dict()

        # Accumulate grounding sources
        existing_sources = state.get('web_sources', [])
        if ops_metadata:
            ops_sources = ops_metadata.to_dict().get('web_sources', [])
            merged_sources = existing_sources + [s for s in ops_sources if s not in existing_sources]
        else:
            merged_sources = existing_sources

        return {
            **state,
            'internal_ops': ops_dict,
            'web_sources': merged_sources,
        }

    except Exception as e:
        logger.exception("Error during internal ops research")
        # Non-fatal, continue without internal ops data
        return {
            **state,
            'internal_ops': None,
        }


def classify_and_ops(state: ResearchState) -> ResearchState:
    """Run vertical classification and internal ops research in parallel (P3 speed-up).

    Both tasks are independent — they share only the research_report context —
    so running them concurrently halves the wall-clock time for this stage.
    internal_ops receives an empty vertical string and uses it only as a hint.
    """
    if state.get('status') in ('failed', 'partial'):
        return state

    _update_job_step(state.get('job_id'), 'classify+ops')

    def _run_classify():
        from ..services.gemini import GeminiClient
        from ..services.classifier import VerticalClassifier
        gemini_client = GeminiClient()
        classifier = VerticalClassifier(gemini_client=gemini_client)
        report = state.get('research_report', {})
        return classifier.classify(
            client_name=state.get('client_name', ''),
            company_overview=report.get('company_overview', ''),
            use_llm=True,
        )

    def _run_internal_ops():
        from ..services.gemini import GeminiClient
        from ..services.internal_ops import InternalOpsService
        gemini_client = GeminiClient()
        svc = InternalOpsService(gemini_client)
        report = state.get('research_report', {})
        return svc.research_internal_ops(
            client_name=state.get('client_name', ''),
            vertical=state.get('vertical', ''),  # may be empty — used as context hint only
            website=report.get('website', ''),
            company_overview=report.get('company_overview', ''),
        )

    vertical = 'other'
    internal_ops_dict = None
    new_sources: list = []

    with ThreadPoolExecutor(max_workers=2) as pool:
        classify_future = pool.submit(_run_classify)
        ops_future = pool.submit(_run_internal_ops)

        try:
            vertical = classify_future.result()
        except Exception:
            logger.exception("Error during parallel vertical classification")

        try:
            ops_data, ops_metadata = ops_future.result()
            internal_ops_dict = ops_data.to_dict()
            if ops_metadata:
                new_sources = ops_metadata.to_dict().get('web_sources', [])
        except Exception:
            logger.exception("Error during parallel internal ops research")

    existing_sources = state.get('web_sources') or []
    merged_sources = existing_sources + [s for s in new_sources if s not in existing_sources]

    return {
        **state,
        'status': 'competitor_search',
        'vertical': vertical,
        'internal_ops': internal_ops_dict,
        'web_sources': merged_sources,
    }


def correlate_internal_ops(state: ResearchState) -> ResearchState:
    """Correlate gap analysis findings with internal ops evidence (AGE-20)."""
    if state.get('status') in ('failed', 'partial'):
        return state

    _update_job_step(state.get('job_id'), 'correlate')

    gap_analysis = state.get('gap_analysis')
    internal_ops = state.get('internal_ops')

    # Skip correlation if either is missing
    if not gap_analysis or not internal_ops:
        logger.info("Skipping gap correlation - missing gap_analysis or internal_ops")
        return {
            **state,
            'status': 'completed',
            'gap_correlations': [],
        }

    try:
        from ..services.gemini import GeminiClient
        from ..services.gap_correlation import GapCorrelationService

        gemini_client = GeminiClient()
        correlation_service = GapCorrelationService(gemini_client)

        correlations = correlation_service.correlate_gaps(
            client_name=state.get('client_name', ''),
            vertical=state.get('vertical', 'other'),
            gap_analysis=gap_analysis,
            internal_ops=internal_ops,
        )

        # Convert to list of dicts
        correlations_list = correlation_service.correlations_to_dict(correlations)

        return {
            **state,
            'status': 'completed',
            'gap_correlations': correlations_list,
        }

    except Exception as e:
        logger.exception("Error during gap correlation")
        # Non-fatal, continue without correlations
        return {
            **state,
            'status': 'completed',
            'gap_correlations': [],
        }


def finalize_result(state: ResearchState) -> ResearchState:
    """Finalize the research result and persist to database."""
    if state.get('status') == 'failed':
        return state

    is_partial = state.get('status') == 'partial'

    from ..models import ResearchJob, ResearchReport, CompetitorCaseStudy, GapAnalysis, InternalOpsIntel

    job_id = state.get('job_id')
    _update_job_step(job_id, 'finalize')
    if not job_id:
        logger.warning("No job_id in state, skipping database persistence")
        return {**state, 'status': 'completed'}

    try:
        job = ResearchJob.objects.get(id=job_id)
    except Exception as e:
        logger.exception("Error fetching ResearchJob during finalization")
        return {**state, 'status': 'completed'}

    # Save vertical to job
    try:
        if state.get('vertical'):
            job.vertical = state['vertical']
            job.save(update_fields=['vertical'])
    except Exception:
        logger.exception("Error saving vertical for job %s", job_id)

    # Create ResearchReport — wrapped in its own savepoint so a validation error
    # (e.g. URLField rejecting a bare domain like "fhlbatl.com") aborts only this
    # savepoint and does NOT poison the outer PostgreSQL transaction, which would
    # otherwise cause all subsequent job.save() calls to silently fail.
    try:
        report_data = state.get('research_report', {}) or {}
        founded_year = report_data.get('founded_year')
        if founded_year is not None:
            try:
                founded_year = int(founded_year)
            except (ValueError, TypeError):
                founded_year = None

        raw_website = report_data.get('website', '') or ''
        if raw_website and '://' not in raw_website:
            raw_website = f'https://{raw_website}'

        with transaction.atomic():
            ResearchReport.objects.update_or_create(
                research_job=job,
                defaults={
                    'company_overview': report_data.get('company_overview', ''),
                    'founded_year': founded_year,
                    'headquarters': report_data.get('headquarters', ''),
                    'employee_count': report_data.get('employee_count', ''),
                    'annual_revenue': report_data.get('annual_revenue', ''),
                    'website': raw_website,
                    'recent_news': report_data.get('recent_news', []),
                    'decision_makers': report_data.get('decision_makers', []),
                    'pain_points': report_data.get('pain_points', []),
                    'opportunities': report_data.get('opportunities', []),
                    'digital_maturity': report_data.get('digital_maturity', ''),
                    'ai_footprint': report_data.get('ai_footprint', ''),
                    'ai_adoption_stage': report_data.get('ai_adoption_stage', ''),
                    'strategic_goals': report_data.get('strategic_goals', []),
                    'key_initiatives': report_data.get('key_initiatives', []),
                    'talking_points': report_data.get('talking_points', []),
                    'cloud_footprint': report_data.get('cloud_footprint', ''),
                    'security_posture': report_data.get('security_posture', ''),
                    'data_maturity': report_data.get('data_maturity', ''),
                    'financial_signals': report_data.get('financial_signals', []),
                    'tech_partnerships': report_data.get('tech_partnerships', []),
                    'web_sources': state.get('web_sources', []),
                    'synthesis_text': state.get('synthesis_text', ''),
                }
            )
        logger.info(f"ResearchReport saved for job {job_id}")
    except Exception as e:
        logger.exception("Error saving ResearchReport for job %s", job_id)

    # Create CompetitorCaseStudy records — per-record isolation so one bad entry cannot
    # wipe all others.  The delete still runs first to prevent duplicates on retry.
    case_studies = state.get('competitor_case_studies', [])
    CompetitorCaseStudy.objects.filter(research_job=job).delete()
    saved_count = 0
    for cs in case_studies:
        try:
            with transaction.atomic():
                CompetitorCaseStudy.objects.create(
                    research_job=job,
                    competitor_name=cs.get('competitor_name', '')[:255],
                    vertical=cs.get('vertical', '')[:50],
                    case_study_title=cs.get('case_study_title', '')[:500],
                    summary=cs.get('summary', ''),
                    technologies_used=cs.get('technologies_used', []),
                    outcomes=cs.get('outcomes', []),
                    source_url=cs.get('source_url', '')[:2000],
                    relevance_score=cs.get('relevance_score', 0.0),
                )
            saved_count += 1
        except Exception as cs_err:
            logger.warning(
                "Skipped competitor record '%s' for job %s: %s",
                cs.get('competitor_name', 'unknown'), job_id, cs_err,
            )
    logger.info(
        "Saved %d/%d CompetitorCaseStudy records for job %s",
        saved_count, len(case_studies), job_id,
    )

    # Create GapAnalysis record — isolated from competitor save failures
    try:
        gap_data = state.get('gap_analysis')
        if gap_data:
            GapAnalysis.objects.update_or_create(
                research_job=job,
                defaults={
                    'technology_gaps': gap_data.get('technology_gaps', []),
                    'capability_gaps': gap_data.get('capability_gaps', []),
                    'process_gaps': gap_data.get('process_gaps', []),
                    'recommendations': gap_data.get('recommendations', []),
                    'priority_areas': gap_data.get('priority_areas', []),
                    'confidence_score': gap_data.get('confidence_score', 0.0),
                    'analysis_notes': gap_data.get('analysis_notes', ''),
                }
            )
            logger.info(f"GapAnalysis saved for job {job_id}")
    except Exception as e:
        logger.exception("Error saving GapAnalysis for job %s", job_id)

    # Create InternalOpsIntel record — isolated from gap/competitor save failures
    try:
        internal_ops_data = state.get('internal_ops')
        if internal_ops_data:
            InternalOpsIntel.objects.update_or_create(
                research_job=job,
                defaults={
                    'employee_sentiment': internal_ops_data.get('employee_sentiment', {}),
                    'linkedin_presence': internal_ops_data.get('linkedin_presence', {}),
                    'social_media_mentions': internal_ops_data.get('social_media_mentions', []),
                    'job_postings': internal_ops_data.get('job_postings', {}),
                    'news_sentiment': internal_ops_data.get('news_sentiment', {}),
                    'key_insights': internal_ops_data.get('key_insights', []),
                    'gap_correlations': state.get('gap_correlations', []),
                    'confidence_score': internal_ops_data.get('confidence_score', 0.0),
                    'data_freshness': internal_ops_data.get('data_freshness', ''),
                    'analysis_notes': internal_ops_data.get('analysis_notes', ''),
                }
            )
            logger.info(f"InternalOpsIntel saved for job {job_id}")
    except Exception as e:
        logger.exception("Error saving InternalOpsIntel for job %s", job_id)

    logger.info(f"Finalization complete for research job {job_id}")

    # Auto-capture to memory (AGE-17)
    try:
        from memory.services import MemoryCapture
        capture = MemoryCapture()
        capture_result = capture.capture_from_research(job)
        logger.info(f"Memory capture result: {capture_result}")
    except Exception as mem_error:
        logger.warning(f"Memory capture failed (non-fatal): {mem_error}")

    # Persist final status to DB here so the job shows as completed/partial even if the
    # HTTP request handler is interrupted (e.g. Cloud Run timeout).
    final_status = 'partial' if is_partial else 'completed'
    try:
        job.status = final_status
        job.current_step = ''
        job.result = state.get('result', '') or state.get('synthesis_text', '')
        job.error = '; '.join(state.get('warnings') or []) if is_partial else ''
        job.save(update_fields=['status', 'current_step', 'result', 'error'])
        logger.info(f"Job {job_id} persisted as {final_status} in DB")
    except Exception as e:
        logger.exception("Error persisting final job status for %s", job_id)

    return {
        **state,
        'status': final_status,
    }


def _format_research_result(report: dict) -> str:
    """Format the research report as plain text for backward compatibility."""
    sections = []

    if report.get('company_overview'):
        sections.append(f"## Company Overview\n{report['company_overview']}")

    # Company details
    details = []
    if report.get('founded_year'):
        details.append(f"- Founded: {report['founded_year']}")
    if report.get('headquarters'):
        details.append(f"- Headquarters: {report['headquarters']}")
    if report.get('employee_count'):
        details.append(f"- Employees: {report['employee_count']}")
    if report.get('annual_revenue'):
        details.append(f"- Revenue: {report['annual_revenue']}")
    if report.get('website'):
        details.append(f"- Website: {report['website']}")
    if details:
        sections.append(f"## Company Details\n" + "\n".join(details))

    # Recent news
    if report.get('recent_news'):
        news_items = []
        for item in report['recent_news']:
            if isinstance(item, dict):
                news_items.append(f"- **{item.get('title', 'News')}**: {item.get('summary', '')}")
            else:
                news_items.append(f"- {item}")
        sections.append(f"## Recent News\n" + "\n".join(news_items))

    # Decision makers
    if report.get('decision_makers'):
        dm_items = []
        for dm in report['decision_makers']:
            if isinstance(dm, dict):
                dm_items.append(f"- **{dm.get('name', 'Unknown')}** - {dm.get('title', '')}: {dm.get('background', '')}")
            else:
                dm_items.append(f"- {dm}")
        sections.append(f"## Key Decision Makers\n" + "\n".join(dm_items))

    # Pain points
    if report.get('pain_points'):
        sections.append(f"## Pain Points\n" + "\n".join(f"- {p}" for p in report['pain_points']))

    # Opportunities
    if report.get('opportunities'):
        sections.append(f"## Opportunities\n" + "\n".join(f"- {o}" for o in report['opportunities']))

    # Digital maturity
    if report.get('digital_maturity') or report.get('ai_footprint'):
        dm_section = "## Digital & AI Assessment\n"
        if report.get('digital_maturity'):
            dm_section += f"- Digital Maturity: {report['digital_maturity'].title()}\n"
        if report.get('ai_adoption_stage'):
            dm_section += f"- AI Adoption Stage: {report['ai_adoption_stage'].title()}\n"
        if report.get('ai_footprint'):
            dm_section += f"- AI Footprint: {report['ai_footprint']}"
        sections.append(dm_section)

    # Strategic goals
    if report.get('strategic_goals'):
        sections.append(f"## Strategic Goals\n" + "\n".join(f"- {g}" for g in report['strategic_goals']))

    # Key initiatives
    if report.get('key_initiatives'):
        sections.append(f"## Key Initiatives\n" + "\n".join(f"- {i}" for i in report['key_initiatives']))

    # Talking points
    if report.get('talking_points'):
        sections.append(f"## Recommended Talking Points\n" + "\n".join(f"- {t}" for t in report['talking_points']))

    # Cloud & Infrastructure
    if report.get('cloud_footprint'):
        sections.append(f"## Cloud & Infrastructure\n{report['cloud_footprint']}")

    # Security Posture
    if report.get('security_posture'):
        sections.append(f"## Security Posture\n{report['security_posture']}")

    # Data Maturity
    if report.get('data_maturity'):
        sections.append(f"## Data Maturity\n{report['data_maturity']}")

    # Financial Signals
    if report.get('financial_signals'):
        sections.append(f"## Financial Signals\n" + "\n".join(f"- {s}" for s in report['financial_signals']))

    # Technology Partnerships
    if report.get('tech_partnerships'):
        sections.append(f"## Technology Partnerships\n" + "\n".join(f"- {p}" for p in report['tech_partnerships']))

    return "\n\n".join(sections)
