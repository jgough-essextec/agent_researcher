import os
from django.conf import settings
from django.utils import timezone
from osint.graph.state import OsintState
from osint.models import OsintJob
from osint.report.builder import OsintReportBuilder


def finalize_osint(state: OsintState) -> OsintState:
    """Finalize: generate .docx and mark job completed."""
    try:
        job = OsintJob.objects.get(pk=state['job_id'])
        builder = OsintReportBuilder(job)
        builder.add_all_sections()
        file_path = builder.build()

        relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)

        job.report_file.name = relative_path
        job.status = 'completed'
        job.phase5_completed_at = timezone.now()
        job.save(update_fields=['report_file', 'status', 'phase5_completed_at', 'updated_at'])

        return {**state, 'status': 'completed', 'report_file_path': file_path}
    except Exception as exc:
        OsintJob.objects.filter(pk=state['job_id']).update(status='failed', error=str(exc))
        return {**state, 'status': 'failed', 'error': str(exc)}
