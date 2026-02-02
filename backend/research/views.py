import threading
from rest_framework import generics, status
from rest_framework.response import Response
from .models import ResearchJob
from .serializers import ResearchJobCreateSerializer, ResearchJobDetailSerializer
from .graph import research_workflow


def run_research_async(job_id: str):
    """Run research workflow asynchronously."""
    try:
        job = ResearchJob.objects.get(id=job_id)
        job.status = 'running'
        job.save()

        # Run the LangGraph workflow
        initial_state = {
            'client_name': job.client_name,
            'sales_history': job.sales_history,
            'prompt': job.prompt,
            'status': 'pending',
            'result': '',
            'error': '',
        }

        result = research_workflow.invoke(initial_state)

        # Update job with results
        job.status = result.get('status', 'failed')
        job.result = result.get('result', '')
        job.error = result.get('error', '')
        job.save()

    except Exception as e:
        try:
            job = ResearchJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error = str(e)
            job.save()
        except Exception:
            pass


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
