"""Views for the projects app."""
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import Project, Iteration, WorkProduct, Annotation
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateSerializer,
    IterationListSerializer,
    IterationDetailSerializer,
    IterationCreateSerializer,
    WorkProductSerializer,
    WorkProductCreateSerializer,
    AnnotationSerializer,
    AnnotationCreateSerializer,
    TimelineSerializer,
    CompareSerializer,
)
from .services.context import ContextAccumulator
from .services.comparison import IterationComparator

from research.models import ResearchJob
from research.views import run_research_async


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project CRUD operations."""

    queryset = Project.objects.annotate(
        iteration_count=Count('iterations')
    ).order_by('-updated_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateSerializer
        return ProjectDetailSerializer

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get timeline view data for a project."""
        project = self.get_object()
        serializer = TimelineSerializer(project)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        """Compare two iterations of a project."""
        project = self.get_object()

        # Get iteration sequences from query params
        iteration_a_seq = request.query_params.get('a')
        iteration_b_seq = request.query_params.get('b')

        if not iteration_a_seq or not iteration_b_seq:
            return Response(
                {'error': 'Both iteration sequences (a and b) are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            iteration_a = project.iterations.get(sequence=int(iteration_a_seq))
            iteration_b = project.iterations.get(sequence=int(iteration_b_seq))
        except (Iteration.DoesNotExist, ValueError):
            return Response(
                {'error': 'Invalid iteration sequence'},
                status=status.HTTP_404_NOT_FOUND
            )

        comparator = IterationComparator()
        comparison = comparator.compare(iteration_a, iteration_b)

        return Response(comparison)


class IterationListCreateView(generics.ListCreateAPIView):
    """List and create iterations for a project."""

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Iteration.objects.filter(project_id=project_id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IterationCreateSerializer
        return IterationListSerializer

    def perform_create(self, serializer):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])

        # Build inherited context
        accumulator = ContextAccumulator()

        # Create iteration first (sequence will be auto-assigned)
        iteration = serializer.save(project=project)

        # Now build context with the iteration's sequence
        inherited_context = accumulator.build_context(iteration)
        iteration.inherited_context = inherited_context
        iteration.save()


class IterationDetailView(generics.RetrieveAPIView):
    """Get iteration details by sequence number."""

    serializer_class = IterationDetailSerializer

    def get_object(self):
        project_id = self.kwargs['project_id']
        sequence = self.kwargs['sequence']
        return get_object_or_404(
            Iteration,
            project_id=project_id,
            sequence=sequence
        )


class IterationStartView(APIView):
    """Start research for an iteration."""

    def post(self, request, project_id, sequence):
        """Create and start a research job for the iteration."""
        iteration = get_object_or_404(
            Iteration,
            project_id=project_id,
            sequence=sequence
        )

        # Check if iteration already has a research job
        if hasattr(iteration, 'research_job') and iteration.research_job:
            return Response(
                {'error': 'Iteration already has a research job'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the project
        project = iteration.project

        # Build context if needed
        if not iteration.inherited_context and project.context_mode == 'accumulate':
            accumulator = ContextAccumulator()
            iteration.inherited_context = accumulator.build_context(iteration)
            iteration.save()

        # Create research job
        job = ResearchJob.objects.create(
            client_name=project.client_name,
            sales_history=iteration.sales_history,
            prompt=iteration.prompt_override,
            iteration=iteration,
        )

        # Update iteration status
        iteration.status = 'running'
        iteration.save()

        # Run research synchronously within the request
        # Cloud Run timeout is 300s, research takes 1-5 min
        run_research_async(str(job.id))

        # Update iteration status based on job result
        job.refresh_from_db()
        iteration.status = 'completed' if job.status == 'completed' else 'failed'
        iteration.save()

        return Response({
            'iteration_id': str(iteration.id),
            'research_job_id': str(job.id),
            'status': job.status,
        }, status=status.HTTP_201_CREATED)


class WorkProductListCreateView(generics.ListCreateAPIView):
    """List and create work products for a project."""

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return WorkProduct.objects.filter(project_id=project_id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkProductCreateSerializer
        return WorkProductSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = get_object_or_404(
            Project, pk=self.kwargs['project_id']
        )
        return context

    def perform_create(self, serializer):
        serializer.save()


class WorkProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a work product."""

    serializer_class = WorkProductSerializer

    def get_object(self):
        return get_object_or_404(
            WorkProduct,
            project_id=self.kwargs['project_id'],
            pk=self.kwargs['pk']
        )


class AnnotationListCreateView(generics.ListCreateAPIView):
    """List and create annotations for a project."""

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Annotation.objects.filter(project_id=project_id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnnotationCreateSerializer
        return AnnotationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = get_object_or_404(
            Project, pk=self.kwargs['project_id']
        )
        return context


class AnnotationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete an annotation."""

    serializer_class = AnnotationSerializer

    def get_object(self):
        return get_object_or_404(
            Annotation,
            project_id=self.kwargs['project_id'],
            pk=self.kwargs['pk']
        )
