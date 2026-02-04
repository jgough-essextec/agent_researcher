import threading
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ResearchJob, ResearchReport, CompetitorCaseStudy, GapAnalysis
from .serializers import (
    ResearchJobCreateSerializer,
    ResearchJobDetailSerializer,
    ResearchReportSerializer,
    CompetitorCaseStudySerializer,
    GapAnalysisSerializer,
)
from .graph import research_workflow


def run_research_async(job_id: str):
    """Run research workflow asynchronously."""
    try:
        job = ResearchJob.objects.get(id=job_id)
        job.status = 'running'
        job.save()

        # Run the LangGraph workflow with job_id for persistence
        initial_state = {
            'client_name': job.client_name,
            'sales_history': job.sales_history,
            'prompt': job.prompt,
            'job_id': str(job.id),
            'status': 'pending',
            'result': '',
            'error': '',
            'research_report': None,
            'vertical': None,
            'competitor_case_studies': None,
            'gap_analysis': None,
        }

        result = research_workflow.invoke(initial_state)

        # Update job with results
        job.refresh_from_db()
        job.status = 'completed'
        job.result = result.get('result', '')
        job.error = result.get('error', '')
        if result.get('vertical'):
            job.vertical = result['vertical']
        job.save()

    except Exception as e:
        try:
            job = ResearchJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error = str(e)
            job.save()
        except Exception:
            pass


class ResearchJobListView(generics.ListAPIView):
    """View for listing all research jobs."""

    queryset = ResearchJob.objects.all().order_by('-created_at')
    serializer_class = ResearchJobDetailSerializer


class ResearchJobCreateView(generics.CreateAPIView):
    """View for creating a new research job."""

    serializer_class = ResearchJobCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()

        # Start research in background thread
        thread = threading.Thread(target=run_research_async, args=(str(job.id),))
        thread.start()

        # Return job details
        output_serializer = ResearchJobDetailSerializer(job)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class ResearchJobDetailView(generics.RetrieveAPIView):
    """View for retrieving research job details."""

    queryset = ResearchJob.objects.all()
    serializer_class = ResearchJobDetailSerializer


class ResearchReportView(APIView):
    """View for retrieving the structured research report (AGE-10)."""

    def get(self, request, pk):
        try:
            job = ResearchJob.objects.get(pk=pk)
            report = ResearchReport.objects.get(research_job=job)
            serializer = ResearchReportSerializer(report)
            return Response(serializer.data)
        except ResearchJob.DoesNotExist:
            return Response(
                {'error': 'Research job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ResearchReport.DoesNotExist:
            return Response(
                {'error': 'Research report not yet available'},
                status=status.HTTP_404_NOT_FOUND
            )


class CompetitorCaseStudiesView(APIView):
    """View for retrieving competitor case studies (AGE-12)."""

    def get(self, request, pk):
        try:
            job = ResearchJob.objects.get(pk=pk)
            case_studies = CompetitorCaseStudy.objects.filter(research_job=job)
            serializer = CompetitorCaseStudySerializer(case_studies, many=True)
            return Response(serializer.data)
        except ResearchJob.DoesNotExist:
            return Response(
                {'error': 'Research job not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class GapAnalysisView(APIView):
    """View for retrieving gap analysis (AGE-13)."""

    def get(self, request, pk):
        try:
            job = ResearchJob.objects.get(pk=pk)
            gap_analysis = GapAnalysis.objects.get(research_job=job)
            serializer = GapAnalysisSerializer(gap_analysis)
            return Response(serializer.data)
        except ResearchJob.DoesNotExist:
            return Response(
                {'error': 'Research job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except GapAnalysis.DoesNotExist:
            return Response(
                {'error': 'Gap analysis not yet available'},
                status=status.HTTP_404_NOT_FOUND
            )
