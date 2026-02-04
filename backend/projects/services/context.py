"""Context accumulation service for iterative research."""
from typing import Optional
from django.db.models import QuerySet

from projects.models import Project, Iteration, WorkProduct, Annotation


class ContextAccumulator:
    """Builds inherited context from previous iterations."""

    def build_context(self, iteration: Iteration) -> dict:
        """
        Build context to inherit from previous iterations.

        Args:
            iteration: The iteration to build context for

        Returns:
            Dictionary containing inherited context
        """
        if iteration.project.context_mode == 'fresh':
            return {}

        # Get previous iteration
        prev = Iteration.objects.filter(
            project=iteration.project,
            sequence__lt=iteration.sequence
        ).order_by('-sequence').first()

        if not prev:
            return {}

        # Check if previous iteration has a research job
        if not hasattr(prev, 'research_job') or not prev.research_job:
            return {}

        context = {
            'previous_iteration_summary': self._summarize_iteration(prev),
            'previous_report_summary': self._summarize_report(prev),
            'identified_pain_points': self._get_pain_points(prev),
            'identified_opportunities': self._get_opportunities(prev),
            'promising_use_cases': self._get_use_cases(prev),
            'starred_plays': self._get_starred_plays(iteration.project),
            'user_notes': self._get_annotations(iteration.project),
        }

        # Filter out empty values
        return {k: v for k, v in context.items() if v}

    def _summarize_iteration(self, iteration: Iteration) -> Optional[dict]:
        """Get summary info about an iteration."""
        if not hasattr(iteration, 'research_job') or not iteration.research_job:
            return None

        job = iteration.research_job
        return {
            'sequence': iteration.sequence,
            'name': iteration.name or f"Iteration {iteration.sequence}",
            'client_name': job.client_name,
            'status': job.status,
            'created_at': iteration.created_at.isoformat(),
        }

    def _summarize_report(self, iteration: Iteration) -> Optional[dict]:
        """Extract key information from previous research report."""
        if not hasattr(iteration, 'research_job') or not iteration.research_job:
            return None

        job = iteration.research_job
        if not hasattr(job, 'report') or not job.report:
            return None

        report = job.report
        return {
            'company_overview': report.company_overview,
            'digital_maturity': report.digital_maturity,
            'ai_adoption_stage': report.ai_adoption_stage,
            'ai_footprint': report.ai_footprint,
            'key_initiatives': report.key_initiatives,
            'strategic_goals': report.strategic_goals,
        }

    def _get_pain_points(self, iteration: Iteration) -> list:
        """Extract pain points from previous iteration."""
        if not hasattr(iteration, 'research_job') or not iteration.research_job:
            return []

        job = iteration.research_job
        if not hasattr(job, 'report') or not job.report:
            return []

        return job.report.pain_points or []

    def _get_opportunities(self, iteration: Iteration) -> list:
        """Extract opportunities from previous iteration."""
        if not hasattr(iteration, 'research_job') or not iteration.research_job:
            return []

        job = iteration.research_job
        if not hasattr(job, 'report') or not job.report:
            return []

        return job.report.opportunities or []

    def _get_use_cases(self, iteration: Iteration) -> list:
        """Extract promising use cases from previous iteration."""
        if not hasattr(iteration, 'research_job') or not iteration.research_job:
            return []

        job = iteration.research_job
        use_cases = job.use_cases.filter(priority='high')[:5]

        return [
            {
                'title': uc.title,
                'description': uc.description,
                'business_problem': uc.business_problem,
                'impact_score': uc.impact_score,
                'feasibility_score': uc.feasibility_score,
            }
            for uc in use_cases
        ]

    def _get_starred_plays(self, project: Project) -> list:
        """Get starred work products (plays) from the project."""
        work_products = project.work_products.filter(
            starred=True,
            category='play'
        ).select_related('content_type')[:10]

        plays = []
        for wp in work_products:
            try:
                obj = wp.content_object
                if obj:
                    plays.append({
                        'title': getattr(obj, 'title', str(obj)),
                        'value_proposition': getattr(obj, 'value_proposition', ''),
                        'elevator_pitch': getattr(obj, 'elevator_pitch', ''),
                        'iteration_sequence': wp.source_iteration.sequence if wp.source_iteration else None,
                        'notes': wp.notes,
                    })
            except Exception:
                continue

        return plays

    def _get_annotations(self, project: Project) -> list:
        """Get user annotations from the project."""
        annotations = project.annotations.all()[:20]

        return [
            {
                'text': ann.text,
                'created_at': ann.created_at.isoformat(),
            }
            for ann in annotations
        ]

    def get_cumulative_context(self, iteration: Iteration) -> dict:
        """
        Build cumulative context from ALL previous iterations.

        This provides a more comprehensive view for later iterations.
        """
        if iteration.project.context_mode == 'fresh':
            return {}

        all_previous = Iteration.objects.filter(
            project=iteration.project,
            sequence__lt=iteration.sequence
        ).order_by('sequence')

        all_pain_points = []
        all_opportunities = []
        all_use_cases = []

        for prev_iter in all_previous:
            all_pain_points.extend(self._get_pain_points(prev_iter))
            all_opportunities.extend(self._get_opportunities(prev_iter))
            all_use_cases.extend(self._get_use_cases(prev_iter))

        # Deduplicate by simple string matching
        unique_pain_points = list(dict.fromkeys(all_pain_points))
        unique_opportunities = list(dict.fromkeys(all_opportunities))

        # For use cases, deduplicate by title
        seen_titles = set()
        unique_use_cases = []
        for uc in all_use_cases:
            if uc['title'] not in seen_titles:
                seen_titles.add(uc['title'])
                unique_use_cases.append(uc)

        context = {
            'iteration_count': all_previous.count(),
            'cumulative_pain_points': unique_pain_points,
            'cumulative_opportunities': unique_opportunities,
            'cumulative_use_cases': unique_use_cases,
            'starred_plays': self._get_starred_plays(iteration.project),
            'user_notes': self._get_annotations(iteration.project),
        }

        return {k: v for k, v in context.items() if v}
