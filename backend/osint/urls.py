from django.urls import path
from . import views

urlpatterns = [
    path('jobs/', views.OsintJobListCreateView.as_view(), name='osint-job-list-create'),
    path('jobs/<uuid:pk>/', views.OsintJobDetailView.as_view(), name='osint-job-detail'),
    path('jobs/<uuid:pk>/execute/', views.OsintJobExecuteView.as_view(), name='osint-job-execute'),
    path('jobs/<uuid:pk>/commands/', views.OsintCommandsView.as_view(), name='osint-commands'),
    path('jobs/<uuid:pk>/submit-terminal-output/', views.SubmitTerminalOutputView.as_view(), name='osint-submit-terminal'),
    path('jobs/<uuid:pk>/submit-screenshots/', views.SubmitScreenshotsView.as_view(), name='osint-submit-screenshots'),
    path('jobs/<uuid:pk>/skip-screenshots/', views.SkipScreenshotsView.as_view(), name='osint-skip-screenshots'),
    path('jobs/<uuid:pk>/generate-report/', views.GenerateReportView.as_view(), name='osint-generate-report'),
    path('jobs/<uuid:pk>/report/', views.DownloadReportView.as_view(), name='osint-download-report'),
    path('jobs/<uuid:pk>/subdomains/', views.SubdomainListView.as_view(), name='osint-subdomains'),
    path('jobs/<uuid:pk>/dns/', views.DnsFindingListView.as_view(), name='osint-dns'),
    path('jobs/<uuid:pk>/email-security/', views.EmailSecurityListView.as_view(), name='osint-email-security'),
    path('jobs/<uuid:pk>/infrastructure/', views.InfrastructureListView.as_view(), name='osint-infrastructure'),
    path('jobs/<uuid:pk>/service-mappings/', views.ServiceMappingListView.as_view(), name='osint-service-mappings'),
]
