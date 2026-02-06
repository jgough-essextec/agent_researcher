from django.urls import path
from . import views

urlpatterns = [
    path('', views.ResearchJobCreateView.as_view(), name='research-create'),
    path('jobs/', views.ResearchJobListView.as_view(), name='research-list'),
    path('<uuid:pk>/', views.ResearchJobDetailView.as_view(), name='research-detail'),
    path('<uuid:pk>/execute/', views.ResearchJobExecuteView.as_view(), name='research-execute'),
    path('<uuid:pk>/report/', views.ResearchReportView.as_view(), name='research-report'),
    path('<uuid:pk>/competitors/', views.CompetitorCaseStudiesView.as_view(), name='research-competitors'),
    path('<uuid:pk>/gaps/', views.GapAnalysisView.as_view(), name='research-gaps'),
    path('<uuid:pk>/export/pdf/', views.ResearchPdfExportView.as_view(), name='research-export-pdf'),
]
