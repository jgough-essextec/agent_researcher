"""URL configuration for the projects app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectViewSet,
    IterationListCreateView,
    IterationDetailView,
    IterationStartView,
    WorkProductListCreateView,
    WorkProductDetailView,
    AnnotationListCreateView,
    AnnotationDetailView,
)

router = DefaultRouter()
router.register(r'', ProjectViewSet, basename='project')

urlpatterns = [
    # Project CRUD via router
    path('', include(router.urls)),

    # Iteration endpoints
    path(
        '<uuid:project_id>/iterations/',
        IterationListCreateView.as_view(),
        name='iteration-list-create'
    ),
    path(
        '<uuid:project_id>/iterations/<int:sequence>/',
        IterationDetailView.as_view(),
        name='iteration-detail'
    ),
    path(
        '<uuid:project_id>/iterations/<int:sequence>/start/',
        IterationStartView.as_view(),
        name='iteration-start'
    ),

    # Work product endpoints
    path(
        '<uuid:project_id>/work-products/',
        WorkProductListCreateView.as_view(),
        name='work-product-list-create'
    ),
    path(
        '<uuid:project_id>/work-products/<uuid:pk>/',
        WorkProductDetailView.as_view(),
        name='work-product-detail'
    ),

    # Annotation endpoints
    path(
        '<uuid:project_id>/annotations/',
        AnnotationListCreateView.as_view(),
        name='annotation-list-create'
    ),
    path(
        '<uuid:project_id>/annotations/<uuid:pk>/',
        AnnotationDetailView.as_view(),
        name='annotation-detail'
    ),
]
