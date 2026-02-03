"""Memory capture service for auto-capturing research insights (AGE-17)."""
import logging
from typing import Optional, Dict, Any
from django.db import transaction

logger = logging.getLogger(__name__)


class MemoryCapture:
    """Service for automatically capturing and storing research insights."""

    def __init__(self, vector_store=None):
        """Initialize the memory capture service.

        Args:
            vector_store: VectorStore instance (lazy loaded if not provided)
        """
        self._vector_store = vector_store

    @property
    def vector_store(self):
        """Lazy initialization of vector store."""
        if self._vector_store is None:
            from .vectorstore import VectorStore
            self._vector_store = VectorStore()
        return self._vector_store

    @transaction.atomic
    def capture_from_research(self, research_job) -> Dict[str, Any]:
        """Capture insights from a completed research job.

        Args:
            research_job: ResearchJob model instance

        Returns:
            Dict with capture results
        """
        from ..models import ClientProfile, MemoryEntry

        results = {
            'client_profile_created': False,
            'memory_entries_created': 0,
            'errors': [],
        }

        try:
            # Create or update client profile
            profile, created = self._capture_client_profile(research_job)
            if profile:
                results['client_profile_created'] = created
                results['client_profile_id'] = str(profile.id)

            # Capture key insights as memory entries
            entries_count = self._capture_insights(research_job)
            results['memory_entries_created'] = entries_count

        except Exception as e:
            logger.exception("Error capturing from research")
            results['errors'].append(str(e))

        return results

    def _capture_client_profile(self, research_job):
        """Create or update client profile from research.

        Args:
            research_job: ResearchJob model instance

        Returns:
            Tuple of (ClientProfile, created)
        """
        from ..models import ClientProfile

        # Try to get the research report
        report = getattr(research_job, 'report', None)

        # Build summary from available data
        summary_parts = []
        if report:
            if report.company_overview:
                summary_parts.append(report.company_overview)
            if report.ai_footprint:
                summary_parts.append(f"AI Footprint: {report.ai_footprint}")
            if report.pain_points:
                summary_parts.append(f"Pain Points: {', '.join(report.pain_points[:3])}")

        summary = ' '.join(summary_parts) or research_job.result[:500]

        # Create or update profile
        profile, created = ClientProfile.objects.update_or_create(
            client_name=research_job.client_name,
            defaults={
                'industry': research_job.vertical or '',
                'summary': summary,
            }
        )

        # Update vector store
        if summary:
            vector_id = f"profile_{profile.id}"
            self.vector_store.add_document(
                'client_profiles',
                vector_id,
                summary,
                metadata={
                    'client_name': research_job.client_name,
                    'industry': research_job.vertical or '',
                    'profile_id': str(profile.id),
                }
            )
            profile.vector_id = vector_id
            profile.save(update_fields=['vector_id'])

        return profile, created

    def _capture_insights(self, research_job) -> int:
        """Capture key insights as memory entries.

        Args:
            research_job: ResearchJob model instance

        Returns:
            Number of entries created
        """
        from ..models import MemoryEntry

        report = getattr(research_job, 'report', None)
        if not report:
            return 0

        entries_created = 0

        # Capture talking points as best practices
        if report.talking_points:
            for i, point in enumerate(report.talking_points[:3]):
                entry = MemoryEntry.objects.create(
                    entry_type='best_practice',
                    title=f"Talking point for {research_job.client_name}",
                    content=point,
                    client_name=research_job.client_name,
                    industry=research_job.vertical or '',
                    source_type='research_job',
                    source_id=str(research_job.id),
                )

                # Add to vector store
                vector_id = f"entry_{entry.id}"
                self.vector_store.add_document(
                    'memory_entries',
                    vector_id,
                    point,
                    metadata={
                        'entry_type': 'best_practice',
                        'title': entry.title,
                        'client_name': research_job.client_name,
                        'industry': research_job.vertical or '',
                    }
                )
                entry.vector_id = vector_id
                entry.save(update_fields=['vector_id'])
                entries_created += 1

        # Capture opportunities as research insights
        if report.opportunities:
            for opportunity in report.opportunities[:2]:
                entry = MemoryEntry.objects.create(
                    entry_type='research_insight',
                    title=f"Opportunity at {research_job.client_name}",
                    content=opportunity,
                    client_name=research_job.client_name,
                    industry=research_job.vertical or '',
                    source_type='research_job',
                    source_id=str(research_job.id),
                )

                vector_id = f"entry_{entry.id}"
                self.vector_store.add_document(
                    'memory_entries',
                    vector_id,
                    opportunity,
                    metadata={
                        'entry_type': 'research_insight',
                        'title': entry.title,
                        'client_name': research_job.client_name,
                        'industry': research_job.vertical or '',
                    }
                )
                entry.vector_id = vector_id
                entry.save(update_fields=['vector_id'])
                entries_created += 1

        return entries_created

    def add_sales_play(
        self,
        title: str,
        play_type: str,
        content: str,
        context: str = "",
        industry: str = "",
        vertical: str = "",
    ):
        """Manually add a sales play to the knowledge base.

        Args:
            title: Title of the sales play
            play_type: Type of play (pitch, objection_handler, etc.)
            content: The play content
            context: When to use this play
            industry: Target industry
            vertical: Target vertical

        Returns:
            Created SalesPlay instance
        """
        from ..models import SalesPlay

        play = SalesPlay.objects.create(
            title=title,
            play_type=play_type,
            content=content,
            context=context,
            industry=industry,
            vertical=vertical,
        )

        # Add to vector store
        vector_id = f"play_{play.id}"
        searchable_content = f"{title} {content} {context}"
        self.vector_store.add_document(
            'sales_plays',
            vector_id,
            searchable_content,
            metadata={
                'title': title,
                'play_type': play_type,
                'industry': industry,
                'vertical': vertical,
                'play_id': str(play.id),
            }
        )
        play.vector_id = vector_id
        play.save(update_fields=['vector_id'])

        return play
