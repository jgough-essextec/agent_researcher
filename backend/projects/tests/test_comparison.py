"""Tests for the IterationComparator service."""
import pytest
from unittest.mock import MagicMock
from projects.services.comparison import IterationComparator


def make_iteration(sequence=1, status='completed', name=None, report_data=None):
    """Create a mock Iteration with optional report data."""
    iteration = MagicMock()
    iteration.id = f'iter-{sequence}'
    iteration.sequence = sequence
    iteration.name = name
    iteration.status = status
    iteration.created_at.isoformat.return_value = '2026-01-01T00:00:00'

    if report_data:
        job = MagicMock()
        job.id = f'job-{sequence}'
        job.client_name = 'Acme Corp'
        job.status = 'completed'
        job.vertical = 'retail'
        job.use_cases.count.return_value = report_data.get('use_cases_count', 0)
        job.personas.count.return_value = report_data.get('personas_count', 0)
        job.competitor_case_studies.count.return_value = 0

        report = MagicMock()
        report.company_overview = report_data.get('company_overview', '')
        report.pain_points = report_data.get('pain_points', [])
        report.opportunities = report_data.get('opportunities', [])
        report.digital_maturity = report_data.get('digital_maturity', 'nascent')
        report.ai_adoption_stage = report_data.get('ai_adoption_stage', 'none')
        report.talking_points = report_data.get('talking_points', [])
        report.decision_makers = report_data.get('decision_makers', [])
        job.report = report
        iteration.research_job = job
    else:
        iteration.research_job = None

    return iteration


class TestIterationComparator:
    def test_compare_returns_correct_keys(self):
        comp = IterationComparator()
        iter_a = make_iteration(sequence=1)
        iter_b = make_iteration(sequence=2)
        result = comp.compare(iter_a, iter_b)
        assert 'iteration_a' in result
        assert 'iteration_b' in result
        assert 'differences' in result

    def test_extract_iteration_data_basic(self):
        comp = IterationComparator()
        iteration = make_iteration(sequence=1, status='completed')
        data = comp._extract_iteration_data(iteration)
        assert data['sequence'] == 1
        assert data['status'] == 'completed'

    def test_extract_iteration_data_default_name(self):
        comp = IterationComparator()
        iteration = make_iteration(sequence=3, name=None)
        data = comp._extract_iteration_data(iteration)
        assert data['name'] == 'Iteration 3'

    def test_extract_iteration_data_custom_name(self):
        comp = IterationComparator()
        iteration = make_iteration(sequence=1, name='Q1 Research')
        data = comp._extract_iteration_data(iteration)
        assert data['name'] == 'Q1 Research'

    def test_extract_iteration_data_with_report(self):
        comp = IterationComparator()
        iteration = make_iteration(
            sequence=1,
            report_data={'pain_points': ['Cost', 'Complexity'], 'opportunities': ['Cloud'], 'use_cases_count': 3}
        )
        data = comp._extract_iteration_data(iteration)
        assert 'report' in data
        assert data['report']['pain_points'] == ['Cost', 'Complexity']
        assert data['use_cases_count'] == 3

    def test_compute_differences_added_items(self):
        comp = IterationComparator()
        iter_a = make_iteration(1, report_data={'pain_points': ['Cost']})
        iter_b = make_iteration(2, report_data={'pain_points': ['Cost', 'Complexity']})
        diffs = comp._compute_differences(iter_a, iter_b)
        assert 'Complexity' in diffs['pain_points']['added']
        assert 'Cost' in diffs['pain_points']['unchanged']

    def test_compute_differences_removed_items(self):
        comp = IterationComparator()
        iter_a = make_iteration(1, report_data={'opportunities': ['Cloud', 'AI']})
        iter_b = make_iteration(2, report_data={'opportunities': ['Cloud']})
        diffs = comp._compute_differences(iter_a, iter_b)
        assert 'AI' in diffs['opportunities']['removed']
        assert 'Cloud' in diffs['opportunities']['unchanged']

    def test_diff_lists_empty(self):
        comp = IterationComparator()
        result = comp._diff_lists([], [])
        assert result == {'added': [], 'removed': [], 'unchanged': []}

    def test_no_report_returns_empty_lists(self):
        comp = IterationComparator()
        iteration = make_iteration(sequence=1)
        assert comp._get_pain_points(iteration) == []
        assert comp._get_opportunities(iteration) == []
        assert comp._get_talking_points(iteration) == []
