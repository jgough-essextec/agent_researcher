"""Iteration comparison service."""
from typing import Optional
from projects.models import Iteration


class IterationComparator:
    """Compare two iterations side-by-side."""

    def compare(self, iteration_a: Iteration, iteration_b: Iteration) -> dict:
        """
        Compare two iterations and return differences.

        Args:
            iteration_a: First iteration (typically earlier)
            iteration_b: Second iteration (typically later)

        Returns:
            Dictionary containing comparison data
        """
        return {
            'iteration_a': self._extract_iteration_data(iteration_a),
            'iteration_b': self._extract_iteration_data(iteration_b),
            'differences': self._compute_differences(iteration_a, iteration_b),
        }

    def _extract_iteration_data(self, iteration: Iteration) -> dict:
        """Extract comparison-relevant data from an iteration."""
        data = {
            'id': str(iteration.id),
            'sequence': iteration.sequence,
            'name': iteration.name or f"Iteration {iteration.sequence}",
            'status': iteration.status,
            'created_at': iteration.created_at.isoformat(),
        }

        # Add research job data if available
        if hasattr(iteration, 'research_job') and iteration.research_job:
            job = iteration.research_job
            data['research_job'] = {
                'id': str(job.id),
                'client_name': job.client_name,
                'status': job.status,
                'vertical': job.vertical,
            }

            # Add report data
            if hasattr(job, 'report') and job.report:
                report = job.report
                data['report'] = {
                    'company_overview': report.company_overview,
                    'pain_points': report.pain_points,
                    'opportunities': report.opportunities,
                    'digital_maturity': report.digital_maturity,
                    'ai_adoption_stage': report.ai_adoption_stage,
                    'talking_points': report.talking_points,
                    'decision_makers': report.decision_makers,
                }

            # Add gap analysis
            if hasattr(job, 'gap_analysis') and job.gap_analysis:
                gap = job.gap_analysis
                data['gap_analysis'] = {
                    'technology_gaps': gap.technology_gaps,
                    'capability_gaps': gap.capability_gaps,
                    'process_gaps': gap.process_gaps,
                    'recommendations': gap.recommendations,
                    'priority_areas': gap.priority_areas,
                }

            # Add use cases count
            data['use_cases_count'] = job.use_cases.count()

            # Add personas count
            data['personas_count'] = job.personas.count()

            # Add competitor case studies count
            data['competitor_case_studies_count'] = job.competitor_case_studies.count()

        return data

    def _compute_differences(self, iteration_a: Iteration, iteration_b: Iteration) -> dict:
        """Compute differences between two iterations."""
        differences = {
            'pain_points': self._diff_lists(
                self._get_pain_points(iteration_a),
                self._get_pain_points(iteration_b)
            ),
            'opportunities': self._diff_lists(
                self._get_opportunities(iteration_a),
                self._get_opportunities(iteration_b)
            ),
            'talking_points': self._diff_lists(
                self._get_talking_points(iteration_a),
                self._get_talking_points(iteration_b)
            ),
        }

        return differences

    def _diff_lists(self, list_a: list, list_b: list) -> dict:
        """Compute additions and removals between two lists."""
        set_a = set(list_a)
        set_b = set(list_b)

        return {
            'added': list(set_b - set_a),
            'removed': list(set_a - set_b),
            'unchanged': list(set_a & set_b),
        }

    def _get_pain_points(self, iteration: Iteration) -> list:
        """Get pain points from iteration."""
        if not hasattr(iteration, 'research_job') or not iteration.research_job:
            return []
        job = iteration.research_job
        if not hasattr(job, 'report') or not job.report:
            return []
        return job.report.pain_points or []

    def _get_opportunities(self, iteration: Iteration) -> list:
        """Get opportunities from iteration."""
        if not hasattr(iteration, 'research_job') or not iteration.research_job:
            return []
        job = iteration.research_job
        if not hasattr(job, 'report') or not job.report:
            return []
        return job.report.opportunities or []

    def _get_talking_points(self, iteration: Iteration) -> list:
        """Get talking points from iteration."""
        if not hasattr(iteration, 'research_job') or not iteration.research_job:
            return []
        job = iteration.research_job
        if not hasattr(job, 'report') or not job.report:
            return []
        return job.report.talking_points or []
