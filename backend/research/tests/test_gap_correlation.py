"""Tests for research/services/gap_correlation.py."""
import json
from unittest.mock import MagicMock
from research.services.gap_correlation import GapCorrelation, GapCorrelationService


class TestGapCorrelation:
    def test_default_values(self):
        gc = GapCorrelation()
        assert gc.gap_type == ''
        assert gc.evidence_type == 'supporting'
        assert gc.confidence == 0.0

    def test_to_dict(self):
        gc = GapCorrelation(
            gap_type='technology',
            description='Missing cloud',
            evidence='Job postings for cloud engineers',
            evidence_type='supporting',
            confidence=0.85,
            sales_implication='Pitch cloud migration',
        )
        d = gc.to_dict()
        assert d['gap_type'] == 'technology'
        assert d['confidence'] == 0.85
        assert d['evidence_type'] == 'supporting'


def make_mock_gemini(return_value):
    mock = MagicMock()
    mock.generate_text.return_value = return_value
    return mock


def make_gap_analysis():
    return {
        'technology_gaps': ['No cloud infrastructure', 'Legacy ERP'],
        'capability_gaps': ['No data science team'],
        'process_gaps': ['Manual reporting'],
    }


def make_internal_ops():
    return {
        'employee_sentiment': {
            'overall_rating': 3.5,
            'trend': 'declining',
            'positive_themes': ['Good culture'],
            'negative_themes': ['Outdated tools'],
        },
        'job_postings': {
            'total_openings': 45,
            'departments_hiring': {'Engineering': 20},
            'skills_sought': ['Python', 'AWS'],
            'urgency_signals': ['Immediate start'],
            'insights': 'Heavy tech hiring indicates transformation',
        },
        'news_sentiment': {
            'overall_sentiment': 'positive',
            'topics': ['cloud announcement', 'new CTO'],
        },
        'key_insights': ['New CTO from AWS', 'Announced digital transformation initiative'],
    }


class TestGapCorrelationService:
    def test_correlate_gaps_parses_valid_json(self):
        svc = GapCorrelationService(make_mock_gemini(json.dumps({
            'gap_correlations': [
                {
                    'gap_type': 'technology',
                    'description': 'No cloud infrastructure',
                    'evidence': 'Hiring cloud engineers',
                    'evidence_type': 'supporting',
                    'confidence': 0.85,
                    'sales_implication': 'Pitch cloud migration services',
                },
                {
                    'gap_type': 'capability',
                    'description': 'No data science team',
                    'evidence': 'No data science job postings',
                    'evidence_type': 'neutral',
                    'confidence': 0.5,
                    'sales_implication': 'Offer managed data science',
                },
            ],
            'overall_confidence': 0.75,
            'analysis_summary': 'Strong evidence for technology gaps',
        })))

        result = svc.correlate_gaps(
            'Acme Corp', 'retail', make_gap_analysis(), make_internal_ops()
        )
        assert len(result) == 2
        assert result[0].gap_type == 'technology'
        assert result[0].confidence == 0.85
        assert result[1].evidence_type == 'neutral'

    def test_correlate_gaps_strips_markdown_fences(self):
        svc = GapCorrelationService(make_mock_gemini(
            '```json\n{"gap_correlations": [], "overall_confidence": 0.5, "analysis_summary": "none"}\n```'
        ))
        result = svc.correlate_gaps('Acme', 'retail', make_gap_analysis(), make_internal_ops())
        assert result == []

    def test_correlate_gaps_returns_empty_on_invalid_json(self):
        svc = GapCorrelationService(make_mock_gemini('not json'))
        result = svc.correlate_gaps('Acme', 'retail', make_gap_analysis(), make_internal_ops())
        assert result == []

    def test_correlate_gaps_returns_empty_on_exception(self):
        mock = MagicMock()
        mock.generate_text.side_effect = Exception('API down')
        svc = GapCorrelationService(mock)
        result = svc.correlate_gaps('Acme', 'retail', make_gap_analysis(), make_internal_ops())
        assert result == []

    def test_correlate_gaps_handles_empty_gap_analysis(self):
        svc = GapCorrelationService(make_mock_gemini(json.dumps({
            'gap_correlations': [],
            'overall_confidence': 0.0,
            'analysis_summary': 'No gaps to analyze',
        })))
        result = svc.correlate_gaps('Acme', 'retail', {}, {})
        assert result == []

    def test_correlations_to_dict(self):
        svc = GapCorrelationService(MagicMock())
        correlations = [
            GapCorrelation(gap_type='technology', description='No cloud', confidence=0.8),
            GapCorrelation(gap_type='process', description='Manual reporting', confidence=0.6),
        ]
        result = svc.correlations_to_dict(correlations)
        assert len(result) == 2
        assert result[0]['gap_type'] == 'technology'
        assert result[1]['confidence'] == 0.6

    def test_prompt_includes_client_name(self):
        svc = GapCorrelationService(make_mock_gemini(json.dumps({
            'gap_correlations': [], 'overall_confidence': 0.0, 'analysis_summary': ''
        })))
        svc.correlate_gaps('SpecificCorp XYZ', 'fintech', {}, {})
        call_args = svc.gemini_client.generate_text.call_args[0][0]
        assert 'SpecificCorp XYZ' in call_args
