"""Views for the memory/knowledge base API."""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ClientProfile, SalesPlay, MemoryEntry
from .serializers import (
    ClientProfileSerializer,
    SalesPlaySerializer,
    MemoryEntrySerializer,
    ContextQuerySerializer,
)
from .services import ContextInjector, MemoryCapture


class ClientProfileListView(generics.ListCreateAPIView):
    """List and create client profiles."""
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer


class ClientProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a client profile."""
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer


class SalesPlayListView(generics.ListCreateAPIView):
    """List and create sales plays."""
    queryset = SalesPlay.objects.all()
    serializer_class = SalesPlaySerializer


class SalesPlayDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a sales play."""
    queryset = SalesPlay.objects.all()
    serializer_class = SalesPlaySerializer


class MemoryEntryListView(generics.ListCreateAPIView):
    """List and create memory entries."""
    queryset = MemoryEntry.objects.all()
    serializer_class = MemoryEntrySerializer


class MemoryEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a memory entry."""
    queryset = MemoryEntry.objects.all()
    serializer_class = MemoryEntrySerializer


class ContextQueryView(APIView):
    """Query the knowledge base for relevant context."""

    def post(self, request):
        """Query for context based on client name and optional filters.

        Request body:
        {
            "client_name": "Company Name",
            "industry": "technology",  # optional
            "query": "AI transformation"  # optional
        }
        """
        serializer = ContextQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        injector = ContextInjector()
        context = injector.get_context_for_research(
            client_name=serializer.validated_data['client_name'],
            industry=serializer.validated_data.get('industry'),
            query=serializer.validated_data.get('query'),
        )

        return Response({
            'client_profiles': context.client_profiles,
            'sales_plays': context.sales_plays,
            'memory_entries': context.memory_entries,
            'relevance_summary': context.relevance_summary,
            'prompt_context': context.to_prompt_context(),
        })


class CaptureFromResearchView(APIView):
    """Capture insights from a completed research job."""

    def post(self, request, pk):
        """Capture insights from a research job.

        Args:
            pk: Research job UUID
        """
        from research.models import ResearchJob

        try:
            job = ResearchJob.objects.get(pk=pk)
        except ResearchJob.DoesNotExist:
            return Response(
                {'error': 'Research job not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if job.status != 'completed':
            return Response(
                {'error': 'Research job is not completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        capture = MemoryCapture()
        results = capture.capture_from_research(job)

        return Response(results)
