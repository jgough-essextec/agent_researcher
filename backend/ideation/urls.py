"""URL configuration for the ideation app."""
from django.urls import path
from . import views

urlpatterns = [
    # Use cases
    path('use-cases/', views.UseCaseListView.as_view(), name='use-case-list'),
    path('use-cases/generate/', views.GenerateUseCasesView.as_view(), name='use-case-generate'),
    path('use-cases/<uuid:pk>/', views.UseCaseDetailView.as_view(), name='use-case-detail'),
    path('use-cases/<uuid:pk>/assess/', views.AssessFeasibilityView.as_view(), name='use-case-assess'),
    path('use-cases/<uuid:pk>/refine/', views.RefinePlayView.as_view(), name='use-case-refine'),

    # Refined plays
    path('plays/', views.RefinedPlayListView.as_view(), name='play-list'),
    path('plays/<uuid:pk>/', views.RefinedPlayDetailView.as_view(), name='play-detail'),
]
