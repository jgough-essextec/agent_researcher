"""Tests for ideation service classes (use_case_generator, feasibility, play_refiner)."""
import json
import pytest
from unittest.mock import MagicMock, patch
from ideation.services.use_case_generator import UseCaseGenerator, UseCaseData
from ideation.services.feasibility import FeasibilityService, FeasibilityData


# ── UseCaseData dataclass ────────────────────────────────────────────────────


class TestUseCaseData:
    def test_default_values(self):
        uc = UseCaseData()
        assert uc.title == ''
        assert uc.priority == 'medium'
        assert uc.impact_score == 0.0
        assert isinstance(uc.expected_benefits, list)

    def test_custom_values(self):
        uc = UseCaseData(title='AI Forecasting', priority='high', impact_score=0.9)
        assert uc.title == 'AI Forecasting'
        assert uc.priority == 'high'
        assert uc.impact_score == 0.9


# ── UseCaseGenerator ────────────────────────────────────────────────────────


def make_mock_gemini(return_value):
    """Return a mock GeminiClient whose generate_text returns the given value."""
    mock = MagicMock()
    mock.generate_text.return_value = return_value
    return mock


def make_research_job(pain_points=None, opportunities=None):
    job = MagicMock()
    job.client_name = 'Acme Corp'
    job.vertical = 'retail'
    report = MagicMock()
    report.company_overview = 'A retail company.'
    report.pain_points = pain_points or ['High costs', 'Manual processes']
    report.opportunities = opportunities or ['Automation', 'Cloud migration']
    report.digital_maturity = 'developing'
    report.ai_adoption_stage = 'exploring'
    gap = MagicMock(technology_gaps=[], capability_gaps=[], process_gaps=[])
    job.report = report
    job.gap_analysis = gap
    return job


class TestUseCaseGenerator:
    def test_format_gaps_all_empty(self):
        gen = UseCaseGenerator()
        gap = MagicMock(technology_gaps=[], capability_gaps=[], process_gaps=[])
        result = gen._format_gaps(gap)
        assert result == 'Not analyzed'

    def test_format_gaps_with_data(self):
        gen = UseCaseGenerator()
        gap = MagicMock(
            technology_gaps=['Cloud', 'AI'],
            capability_gaps=['Data science'],
            process_gaps=['DevOps']
        )
        result = gen._format_gaps(gap)
        assert 'Cloud' in result
        assert 'Data science' in result

    def test_generate_use_cases_parses_valid_json(self):
        gen = UseCaseGenerator()
        gen._gemini_client = make_mock_gemini(json.dumps({
            'use_cases': [
                {
                    'title': 'AI Demand Forecasting',
                    'description': 'ML-based forecasting',
                    'business_problem': 'Excess inventory',
                    'proposed_solution': 'Deploy Azure ML',
                    'expected_benefits': ['30% cost reduction'],
                    'estimated_roi': '$1M',
                    'time_to_value': '6 months',
                    'technologies': ['Azure ML'],
                    'data_requirements': ['ERP data'],
                    'integration_points': ['SAP'],
                    'priority': 'high',
                    'impact_score': 0.85,
                    'feasibility_score': 0.75,
                }
            ]
        }))

        result = gen.generate_use_cases(make_research_job())
        assert len(result) == 1
        assert result[0].title == 'AI Demand Forecasting'
        assert result[0].priority == 'high'
        assert result[0].impact_score == 0.85

    def test_generate_use_cases_strips_markdown_fences(self):
        gen = UseCaseGenerator()
        gen._gemini_client = make_mock_gemini('```json\n{"use_cases": []}\n```')
        result = gen.generate_use_cases(make_research_job())
        assert result == []

    def test_generate_use_cases_returns_empty_on_invalid_json(self):
        gen = UseCaseGenerator()
        gen._gemini_client = make_mock_gemini('not json at all')
        result = gen.generate_use_cases(make_research_job())
        assert result == []

    def test_generate_use_cases_returns_empty_on_exception(self):
        gen = UseCaseGenerator()
        mock = MagicMock()
        mock.generate_text.side_effect = Exception('API error')
        gen._gemini_client = mock
        result = gen.generate_use_cases(make_research_job())
        assert result == []

    @pytest.mark.django_db
    def test_create_use_case_models(self):
        from research.models import ResearchJob
        from ideation.models import UseCase

        job = ResearchJob.objects.create(client_name='Test Co')
        gen = UseCaseGenerator()
        uc_data = UseCaseData(
            title='Test Use Case',
            description='Test description',
            business_problem='A problem',
            proposed_solution='A solution',
            expected_benefits=['Benefit 1'],
            estimated_roi='$500K',
            time_to_value='3 months',
            technologies=['Python'],
            data_requirements=['DB'],
            integration_points=['API'],
            priority='high',
            impact_score=0.8,
            feasibility_score=0.7,
        )

        created = gen.create_use_case_models(job, [uc_data])
        assert len(created) == 1
        assert created[0].title == 'Test Use Case'
        assert UseCase.objects.filter(research_job=job).count() == 1


# ── FeasibilityData dataclass ────────────────────────────────────────────────


class TestFeasibilityData:
    def test_default_values(self):
        fd = FeasibilityData()
        assert fd.overall_feasibility == 'medium'
        assert fd.overall_score == 0.0
        assert isinstance(fd.technical_risks, list)

    def test_custom_values(self):
        fd = FeasibilityData(overall_feasibility='high', overall_score=0.9)
        assert fd.overall_feasibility == 'high'
        assert fd.overall_score == 0.9


# ── FeasibilityService ────────────────────────────────────────────────────────


def make_use_case_mock():
    uc = MagicMock()
    uc.title = 'AI Forecasting'
    uc.description = 'ML forecasting'
    uc.business_problem = 'High inventory costs'
    uc.proposed_solution = 'Azure ML pipeline'
    uc.technologies = ['Azure ML', 'Power BI']
    uc.data_requirements = ['ERP data']
    uc.integration_points = ['SAP']
    uc.research_job.vertical = 'retail'
    uc.research_job.report.digital_maturity = 'developing'
    uc.research_job.report.ai_adoption_stage = 'exploring'
    return uc


class TestFeasibilityService:
    def test_assess_feasibility_parses_valid_json(self):
        svc = FeasibilityService()
        svc._gemini_client = make_mock_gemini(json.dumps({
            'overall_feasibility': 'high',
            'overall_score': 0.85,
            'technical_complexity': 'Medium',
            'data_availability': 'Good',
            'integration_complexity': 'Low',
            'scalability_considerations': 'Cloud-native',
            'technical_risks': ['Data quality'],
            'mitigation_strategies': ['Data cleansing'],
            'prerequisites': ['ERP access'],
            'dependencies': ['Azure subscription'],
            'recommendations': 'Proceed with pilot',
            'next_steps': ['Define scope'],
        }))

        result = svc.assess_feasibility(make_use_case_mock())
        assert result.overall_feasibility == 'high'
        assert result.overall_score == 0.85
        assert result.technical_risks == ['Data quality']

    def test_assess_feasibility_returns_default_on_invalid_json(self):
        svc = FeasibilityService()
        svc._gemini_client = make_mock_gemini('bad json')
        result = svc.assess_feasibility(make_use_case_mock())
        assert isinstance(result, FeasibilityData)
        assert result.overall_feasibility == 'medium'

    def test_assess_feasibility_returns_default_on_exception(self):
        svc = FeasibilityService()
        mock = MagicMock()
        mock.generate_text.side_effect = Exception('API down')
        svc._gemini_client = mock
        result = svc.assess_feasibility(make_use_case_mock())
        assert isinstance(result, FeasibilityData)
