"""Tests for workflow node functions in research/graph/nodes.py."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from research.models import ResearchJob


# ---------------------------------------------------------------------------
# validate_input
# ---------------------------------------------------------------------------

class TestValidateInput:

    def test_validate_passes_with_client_name_and_api_key(self, settings):
        from research.graph.nodes import validate_input

        settings.GEMINI_API_KEY = 'test-key-123'
        state = {'client_name': 'TestCo', 'status': 'pending'}

        result = validate_input(state)

        assert result['status'] == 'researching'

    def test_validate_fails_without_client_name(self, settings):
        from research.graph.nodes import validate_input

        settings.GEMINI_API_KEY = 'test-key-123'
        state = {'client_name': '', 'status': 'pending'}

        result = validate_input(state)

        assert result['status'] == 'failed'
        assert 'client name' in result['error'].lower()

    def test_validate_fails_without_api_key(self, settings):
        from research.graph.nodes import validate_input

        settings.GEMINI_API_KEY = ''
        state = {'client_name': 'TestCo', 'status': 'pending'}

        result = validate_input(state)

        assert result['status'] == 'failed'
        assert 'api key' in result['error'].lower()

    def test_validate_preserves_other_state_keys(self, settings):
        from research.graph.nodes import validate_input

        settings.GEMINI_API_KEY = 'test-key'
        state = {
            'client_name': 'TestCo',
            'sales_history': 'Some history',
            'job_id': 'abc-123',
            'status': 'pending',
        }

        result = validate_input(state)

        assert result['sales_history'] == 'Some history'
        assert result['job_id'] == 'abc-123'


# ---------------------------------------------------------------------------
# _format_research_result
# ---------------------------------------------------------------------------

class TestFormatResearchResult:

    def test_format_includes_company_overview(self):
        from research.graph.nodes import _format_research_result

        report = {'company_overview': 'A global tech company.'}
        result = _format_research_result(report)

        assert 'Company Overview' in result
        assert 'A global tech company.' in result

    def test_format_includes_all_key_sections(self):
        from research.graph.nodes import _format_research_result

        report = {
            'company_overview': 'Overview text',
            'pain_points': ['Pain 1', 'Pain 2'],
            'opportunities': ['Opportunity 1'],
            'strategic_goals': ['Goal 1'],
            'key_initiatives': ['Initiative 1'],
            'cloud_footprint': 'AWS heavy',
            'security_posture': 'SOC2 compliant',
            'financial_signals': ['Signal 1'],
            'tech_partnerships': ['Microsoft', 'AWS'],
        }

        result = _format_research_result(report)

        assert 'Pain Points' in result
        assert 'Pain 1' in result
        assert 'Opportunities' in result
        assert 'Strategic Goals' in result
        assert 'Cloud & Infrastructure' in result
        assert 'Security Posture' in result
        assert 'Financial Signals' in result

    def test_format_handles_missing_fields_gracefully(self):
        from research.graph.nodes import _format_research_result

        result = _format_research_result({})

        assert isinstance(result, str)

    def test_format_handles_empty_report(self):
        from research.graph.nodes import _format_research_result

        result = _format_research_result({})

        assert result == ""

    def test_format_handles_decision_makers_dict(self):
        from research.graph.nodes import _format_research_result

        report = {
            'decision_makers': [
                {'name': 'Jane Doe', 'title': 'CTO', 'background': 'Ex-Google'},
            ]
        }

        result = _format_research_result(report)

        assert 'Jane Doe' in result
        assert 'CTO' in result


# ---------------------------------------------------------------------------
# conduct_research node
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestConductResearchNode:

    @patch('research.services.gemini.GeminiClient')
    def test_conduct_research_returns_correct_state_keys(self, MockGeminiClient):
        from research.graph.nodes import conduct_research

        mock_client = MockGeminiClient.return_value
        mock_report = Mock()
        mock_report.to_dict.return_value = {
            'company_overview': 'A test company',
            'headquarters': 'New York, NY',
            'employee_count': '10,000',
            'annual_revenue': '$1B',
            'ai_footprint': 'Using ML for recommendations',
            'cloud_footprint': 'AWS',
            'digital_maturity': 'advanced',
            'strategic_goals': ['Goal 1'],
            'key_initiatives': ['Initiative 1'],
            'pain_points': [],
            'opportunities': [],
        }
        mock_metadata = Mock()
        mock_metadata.to_dict.return_value = {'web_sources': [{'uri': 'https://example.com', 'title': 'Example'}]}
        mock_client.conduct_deep_research.return_value = (mock_report, mock_metadata, 'raw synthesis text')

        state = {
            'client_name': 'TestCo',
            'sales_history': '',
            'status': 'researching',
        }

        result = conduct_research(state)

        assert result['status'] == 'classifying'
        assert 'research_report' in result
        assert 'result' in result
        assert 'web_sources' in result
        assert result['research_report']['company_overview'] == 'A test company'

    @patch('research.services.gemini.GeminiClient')
    def test_conduct_research_handles_exception(self, MockGeminiClient):
        from research.graph.nodes import conduct_research

        MockGeminiClient.return_value.conduct_deep_research.side_effect = Exception("API Error")

        state = {
            'client_name': 'TestCo',
            'sales_history': '',
            'status': 'researching',
        }

        result = conduct_research(state)

        assert result['status'] == 'failed'
        assert 'error' in result

    def test_conduct_research_skips_when_already_failed(self):
        from research.graph.nodes import conduct_research

        state = {'status': 'failed', 'error': 'Validation failed', 'client_name': 'TestCo'}
        result = conduct_research(state)

        assert result['status'] == 'failed'


# ---------------------------------------------------------------------------
# finalize_result node
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFinalizeResultNode:

    def test_finalize_skips_when_no_job_id(self):
        from research.graph.nodes import finalize_result

        state = {
            'client_name': 'TestCo',
            'status': 'completed',
            'research_report': {'company_overview': 'Test'},
            'competitor_case_studies': [],
            'gap_analysis': None,
            'internal_ops': None,
            'gap_correlations': [],
        }

        result = finalize_result(state)

        assert result['status'] == 'completed'

    def test_finalize_handles_missing_research_report(self):
        from research.graph.nodes import finalize_result

        job = ResearchJob.objects.create(client_name='TestCo', status='running')

        state = {
            'job_id': str(job.id),
            'client_name': 'TestCo',
            'status': 'completed',
            'research_report': {},
            'competitor_case_studies': [],
            'gap_analysis': None,
            'internal_ops': None,
            'gap_correlations': [],
        }

        result = finalize_result(state)

        assert result['status'] == 'completed'

    def test_finalize_skips_when_status_failed(self):
        from research.graph.nodes import finalize_result

        state = {
            'job_id': 'some-id',
            'status': 'failed',
            'error': 'Research failed',
            'client_name': 'TestCo',
        }

        result = finalize_result(state)

        assert result['status'] == 'failed'

    def test_finalize_saves_gap_analysis(self):
        from research.graph.nodes import finalize_result
        from research.models import GapAnalysis

        job = ResearchJob.objects.create(client_name='TestCo', status='running')

        state = {
            'job_id': str(job.id),
            'client_name': 'TestCo',
            'vertical': 'technology',
            'status': 'completed',
            'research_report': {'company_overview': 'Test', 'founded_year': 2010},
            'competitor_case_studies': [],
            'gap_analysis': {
                'technology_gaps': ['T1'],
                'capability_gaps': [],
                'process_gaps': [],
                'recommendations': ['R1'],
                'priority_areas': ['P1'],
                'confidence_score': 0.75,
                'analysis_notes': 'Notes',
            },
            'internal_ops': None,
            'gap_correlations': [],
        }

        finalize_result(state)

        assert GapAnalysis.objects.filter(research_job=job).exists()
        gap = GapAnalysis.objects.get(research_job=job)
        assert gap.technology_gaps == ['T1']
        assert gap.confidence_score == 0.75


# ---------------------------------------------------------------------------
# Task 3.2 — per-record fault tolerance in finalize_result
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFinalizeResultCompetitorFaultTolerance:
    def test_saves_valid_competitors_when_one_record_fails(self):
        """If one competitor record fails to save, the others are still persisted."""
        from research.graph.nodes import finalize_result
        from research.models import ResearchJob, CompetitorCaseStudy

        job = ResearchJob.objects.create(client_name="FaultTest", status="running")
        state = {
            'job_id': str(job.id),
            'client_name': 'FaultTest',
            'status': 'completed',
            'result': '',
            'research_report': {'company_overview': 'A test company'},
            'competitor_case_studies': [
                {
                    'competitor_name': 'Good Corp',
                    'vertical': 'tech',
                    'case_study_title': 'Good Case',
                    'summary': 'Great outcome.',
                    'technologies_used': ['Python'],
                    'outcomes': ['Success'],
                    'source_url': 'https://valid.example.com',
                    'relevance_score': 0.8,
                },
                {
                    # This record has relevance_score as a string — will fail FloatField
                    'competitor_name': 'Bad Corp',
                    'vertical': 'tech',
                    'case_study_title': 'Bad Case',
                    'summary': 'Bad.',
                    'technologies_used': [],
                    'outcomes': [],
                    'source_url': 'https://bad.example.com',
                    'relevance_score': 'not-a-float',  # causes ValueError on create
                },
                {
                    'competitor_name': 'Also Good Corp',
                    'vertical': 'tech',
                    'case_study_title': 'Also Good Case',
                    'summary': 'Also great.',
                    'technologies_used': [],
                    'outcomes': [],
                    'source_url': 'https://alsovalid.example.com',
                    'relevance_score': 0.6,
                },
            ],
            'gap_analysis': None,
            'internal_ops': None,
            'gap_correlations': [],
            'web_sources': [],
            'synthesis_text': '',
        }

        finalize_result(state)

        saved = CompetitorCaseStudy.objects.filter(research_job=job)
        saved_names = list(saved.values_list('competitor_name', flat=True))
        assert 'Good Corp' in saved_names
        assert 'Also Good Corp' in saved_names
        assert 'Bad Corp' not in saved_names
        assert saved.count() == 2


# ---------------------------------------------------------------------------
# Task 3.3 — warning propagation in search_competitors
# ---------------------------------------------------------------------------

class TestSearchCompetitorsWarning:
    def test_adds_warning_to_state_on_exception(self):
        """search_competitors appends a warning to state when an exception occurs."""
        from research.graph.nodes import search_competitors
        from unittest.mock import patch, MagicMock

        with patch('research.services.competitor.CompetitorSearchService') as MockSvc:
            MockSvc.return_value.search_competitor_case_studies.side_effect = Exception("API timeout")

            with patch('research.services.gemini.GeminiClient'):
                state = {
                    'status': 'competitor_search',
                    'client_name': 'TestCo',
                    'vertical': 'tech',
                    'research_report': {},
                    'web_sources': [],
                }
                result = search_competitors(state)

        assert result['competitor_case_studies'] == []
        assert result['status'] == 'gap_analysis'
        warnings = result.get('warnings', [])
        assert len(warnings) > 0
        assert any('competitor' in w.lower() or 'Competitor' in w for w in warnings)
