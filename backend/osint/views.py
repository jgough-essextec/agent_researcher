import threading

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status as http_status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    OsintJob,
    OsintCommandRound,
    DnsFinding,
    SubdomainFinding,
    InfrastructureFinding,
    EmailSecurityAssessment,
    ScreenshotUpload,
    ServiceMapping,
)
from .serializers import (
    OsintJobCreateSerializer,
    OsintJobSerializer,
    DnsFindingSerializer,
    SubdomainFindingSerializer,
    InfrastructureFindingSerializer,
    EmailSecuritySerializer,
    ServiceMappingSerializer,
)

_NOT_IMPLEMENTED = Response(
    {'detail': 'Not implemented yet.'},
    status=http_status.HTTP_501_NOT_IMPLEMENTED,
)


class OsintJobListCreateView(generics.ListCreateAPIView):
    queryset = OsintJob.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OsintJobCreateSerializer
        return OsintJobSerializer

    def create(self, request, *args, **kwargs):
        create_serializer = OsintJobCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        job = create_serializer.save()
        # Return the full serializer so the response includes id and all fields
        response_serializer = OsintJobSerializer(job)
        return Response(response_serializer.data, status=http_status.HTTP_201_CREATED)


class OsintJobDetailView(generics.RetrieveAPIView):
    queryset = OsintJob.objects.all()
    serializer_class = OsintJobSerializer


class OsintJobExecuteView(APIView):
    def post(self, request: Request, pk) -> Response:
        try:
            with transaction.atomic():
                job = OsintJob.objects.select_for_update().get(pk=pk)
                if job.status not in ('pending', 'failed'):
                    return Response(
                        {'detail': f'Cannot execute job in status: {job.status}'},
                        status=http_status.HTTP_400_BAD_REQUEST,
                    )
                job.status = 'phase1_research'
                job.error = ''
                job.save(update_fields=['status', 'error', 'updated_at'])
        except OsintJob.DoesNotExist:
            return Response(
                {'detail': 'Not found'},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        state = _build_initial_state(job)
        config = {"configurable": {"thread_id": str(job.id)}}

        def _run():
            from osint.graph.workflow import get_graph
            graph = get_graph()
            try:
                graph.invoke(state, config=config)
            except Exception as exc:
                OsintJob.objects.filter(pk=job.id).update(
                    status='failed',
                    error=str(exc),
                )

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        job.refresh_from_db()
        serializer = OsintJobSerializer(job)
        return Response(serializer.data, status=http_status.HTTP_202_ACCEPTED)


def _build_initial_state(job) -> dict:
    prior_context = None
    if job.research_job_id:
        try:
            from research.models import ResearchJob
            prior_job = ResearchJob.objects.get(pk=job.research_job_id)
            prior_context = {
                'company_overview': str(getattr(prior_job, 'report', '') or '')[:500],
            }
        except Exception:
            pass

    return {
        'job_id': str(job.id),
        'organization_name': job.organization_name,
        'primary_domain': job.primary_domain,
        'additional_domains': list(job.additional_domains),
        'engagement_context': job.engagement_context,
        'research_job_id': str(job.research_job_id) if job.research_job_id else None,
        'prior_research_context': prior_context,
        'status': 'pending',
        'error': '',
        'warnings': [],
        'web_research': None,
        'breach_history': None,
        'job_postings_intel': None,
        'regulatory_framework': None,
        'vendor_relationships': None,
        'leadership_intel': None,
        'crt_sh_subdomains': None,
        'dns_records': None,
        'email_security': None,
        'whois_data': None,
        'arin_data': None,
        'terminal_submissions': None,
        'screenshots': None,
        'screenshot_analyses': None,
        'infrastructure_map': None,
        'technology_stack': None,
        'risk_matrix': None,
        'severity_table': None,
        'report_sections': None,
        'service_mappings': None,
        'report_file_path': None,
    }


class OsintCommandsView(APIView):
    def get(self, request: Request, pk) -> Response:
        try:
            job = OsintJob.objects.get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'awaiting_terminal_output':
            return Response(
                {
                    'detail': (
                        f'Commands only available when status is awaiting_terminal_output. '
                        f'Current: {job.status}'
                    )
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        rounds = OsintCommandRound.objects.filter(osint_job=job).order_by('round_number')
        return Response({
            'job_id': str(job.id),
            'organization_name': job.organization_name,
            'primary_domain': job.primary_domain,
            'rounds': [
                {
                    'round_number': r.round_number,
                    'commands': r.commands,
                    'rationale': r.rationale,
                    'output_submitted': r.output_submitted,
                }
                for r in rounds
            ],
        })


class SubmitTerminalOutputView(APIView):
    def post(self, request: Request, pk) -> Response:
        try:
            with transaction.atomic():
                job = OsintJob.objects.select_for_update().get(pk=pk)

                if job.status != 'awaiting_terminal_output':
                    return Response(
                        {'detail': f'Expected awaiting_terminal_output, got {job.status}'},
                        status=http_status.HTTP_400_BAD_REQUEST,
                    )

                submissions = request.data.get('submissions', [])
                if not submissions:
                    return Response(
                        {'detail': 'submissions must be a non-empty list'},
                        status=http_status.HTTP_400_BAD_REQUEST,
                    )

                OsintCommandRound.objects.filter(
                    osint_job=job, output_submitted=False
                ).update(output_submitted=True, submitted_at=timezone.now())

                job.status = 'phase2_processing'
                job.save(update_fields=['status', 'updated_at'])
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        t = threading.Thread(
            target=self._resume_graph,
            args=(str(job.id), list(submissions)),
            daemon=True,
        )
        t.start()

        job.refresh_from_db()
        serializer = OsintJobSerializer(job)
        return Response(serializer.data, status=http_status.HTTP_202_ACCEPTED)

    def _resume_graph(self, job_id: str, submissions: list) -> None:
        from osint.graph.workflow import run_from_terminal_submission
        run_from_terminal_submission(job_id, submissions)


VALID_SOURCES = {'dnsdumpster', 'shodan', 'other'}
MAX_SCREENSHOTS = 20
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class SubmitScreenshotsView(APIView):
    def post(self, request: Request, pk) -> Response:
        try:
            job = OsintJob.objects.get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'awaiting_screenshots':
            return Response(
                {'detail': f'Expected awaiting_screenshots, got {job.status}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        source = request.data.get('source', '')
        if source not in VALID_SOURCES:
            return Response(
                {'detail': f'source must be one of: {", ".join(sorted(VALID_SOURCES))}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        existing_count = ScreenshotUpload.objects.filter(osint_job=job).count()
        if existing_count >= MAX_SCREENSHOTS:
            return Response(
                {'detail': f'Maximum {MAX_SCREENSHOTS} screenshots per job'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES.get('image')
        if not image_file:
            return Response(
                {'detail': 'image file required'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if image_file.size > MAX_FILE_SIZE:
            return Response(
                {'detail': f'File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # Validate it is actually an image using Pillow
        try:
            import io as _io
            from PIL import Image as PilImage
            image_bytes = image_file.read()
            buf = _io.BytesIO(image_bytes)
            img = PilImage.open(buf)
            img.verify()
            image_file.seek(0)
        except Exception:
            return Response(
                {'detail': 'Uploaded file is not a valid image (PNG, JPEG, or WebP required)'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        caption = request.data.get('caption', '')
        screenshot = ScreenshotUpload.objects.create(
            osint_job=job,
            source=source,
            image=image_file,
            caption=caption,
        )

        job.status = 'phase3_processing'
        job.save(update_fields=['status', 'updated_at'])

        screenshot_ids = list(
            ScreenshotUpload.objects.filter(osint_job=job).values_list('id', flat=True)
        )

        t = threading.Thread(
            target=self._resume_graph,
            args=(str(job.id), [str(sid) for sid in screenshot_ids]),
            daemon=True,
        )
        t.start()

        return Response(
            {
                'detail': 'Screenshot uploaded, analysis resuming.',
                'screenshot_id': str(screenshot.id),
            },
            status=http_status.HTTP_202_ACCEPTED,
        )

    def _resume_graph(self, job_id: str, screenshot_ids: list) -> None:
        from osint.graph.workflow import run_from_screenshots
        run_from_screenshots(job_id, screenshot_ids)


class SkipScreenshotsView(APIView):
    def post(self, request: Request, pk) -> Response:
        try:
            job = OsintJob.objects.get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'awaiting_screenshots':
            return Response(
                {'detail': f'Expected awaiting_screenshots, got {job.status}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        job.status = 'phase3_processing'
        job.save(update_fields=['status', 'updated_at'])

        t = threading.Thread(
            target=self._resume_graph,
            args=(str(job.id),),
            daemon=True,
        )
        t.start()

        return Response({'detail': 'Screenshots skipped, analysis will proceed without them.'})

    def _resume_graph(self, job_id: str) -> None:
        from osint.graph.workflow import run_from_screenshots
        run_from_screenshots(job_id, [])


class GenerateReportView(APIView):
    def post(self, request: Request, pk) -> Response:
        try:
            job = OsintJob.objects.select_for_update().get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status not in ('phase4_analysis', 'completed'):
            return Response(
                {'detail': f'Report generation requires phase4_analysis or completed status. Got: {job.status}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        job.status = 'phase5_report'
        job.save(update_fields=['status', 'updated_at'])

        t = threading.Thread(
            target=self._build_report_async,
            args=(str(job.id),),
            daemon=True,
        )
        t.start()

        return Response({'detail': 'Report generation started.'}, status=http_status.HTTP_202_ACCEPTED)

    def _build_report_async(self, job_id: str) -> None:
        try:
            from osint.models import OsintJob as _OsintJob
            from osint.report.builder import OsintReportBuilder
            from django.utils import timezone as _tz

            job = _OsintJob.objects.get(pk=job_id)
            if not job.report_sections.exists():
                from osint.graph.nodes.phase5_report import _generate_all_sections
                state = {
                    'job_id': job_id,
                    'organization_name': job.organization_name,
                    'primary_domain': job.primary_domain,
                    'web_research': None,
                    'email_security': None,
                    'technology_stack': None,
                    'severity_table': None,
                    'service_mappings': None,
                    'crt_sh_subdomains': None,
                }
                _generate_all_sections(state)

            builder = OsintReportBuilder(job)
            builder.add_all_sections()
            file_path = builder.build()

            import os as _os
            from django.conf import settings as _settings
            relative_path = _os.path.relpath(file_path, _settings.MEDIA_ROOT)
            job.report_file.name = relative_path
            job.status = 'completed'
            job.phase5_completed_at = _tz.now()
            job.save(update_fields=['report_file', 'status', 'phase5_completed_at', 'updated_at'])
        except Exception as exc:
            from osint.models import OsintJob as _OsintJob
            _OsintJob.objects.filter(pk=job_id).update(status='failed', error=str(exc))


class DownloadReportView(APIView):
    def get(self, request: Request, pk) -> Response:
        try:
            job = OsintJob.objects.get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'completed' or not job.report_file:
            return Response(
                {'detail': 'Report not yet available'},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        import os
        from django.http import FileResponse

        file_path = job.report_file.path
        if not os.path.exists(file_path):
            return Response(
                {'detail': 'Report file not found on disk'},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        safe_name = "".join(
            c if c.isalnum() or c == '_' else '_'
            for c in job.organization_name
        )
        filename = f"Pellera_OSINT_{safe_name}.docx"

        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class SubdomainListView(generics.ListAPIView):
    serializer_class = SubdomainFindingSerializer

    def get_queryset(self):
        return SubdomainFinding.objects.filter(osint_job_id=self.kwargs['pk'])


class DnsFindingListView(generics.ListAPIView):
    serializer_class = DnsFindingSerializer

    def get_queryset(self):
        return DnsFinding.objects.filter(osint_job_id=self.kwargs['pk'])


class EmailSecurityListView(generics.ListAPIView):
    serializer_class = EmailSecuritySerializer

    def get_queryset(self):
        return EmailSecurityAssessment.objects.filter(osint_job_id=self.kwargs['pk'])


class InfrastructureListView(generics.ListAPIView):
    serializer_class = InfrastructureFindingSerializer

    def get_queryset(self):
        return InfrastructureFinding.objects.filter(osint_job_id=self.kwargs['pk'])


class ServiceMappingListView(generics.ListAPIView):
    serializer_class = ServiceMappingSerializer

    def get_queryset(self):
        return ServiceMapping.objects.filter(osint_job_id=self.kwargs['pk'])
