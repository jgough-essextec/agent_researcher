"""URL configuration for the memory app."""
from django.urls import path
from . import views

urlpatterns = [
    # Client profiles
    path('profiles/', views.ClientProfileListView.as_view(), name='profile-list'),
    path('profiles/<uuid:pk>/', views.ClientProfileDetailView.as_view(), name='profile-detail'),

    # Sales plays
    path('plays/', views.SalesPlayListView.as_view(), name='play-list'),
    path('plays/<uuid:pk>/', views.SalesPlayDetailView.as_view(), name='play-detail'),

    # Memory entries
    path('entries/', views.MemoryEntryListView.as_view(), name='entry-list'),
    path('entries/<uuid:pk>/', views.MemoryEntryDetailView.as_view(), name='entry-detail'),

    # Context query
    path('context/', views.ContextQueryView.as_view(), name='context-query'),

    # Capture from research
    path('capture/<uuid:pk>/', views.CaptureFromResearchView.as_view(), name='capture-from-research'),
]
