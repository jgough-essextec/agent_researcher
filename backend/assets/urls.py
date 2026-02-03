"""URL configuration for the assets app."""
from django.urls import path
from . import views

urlpatterns = [
    # Personas
    path('personas/', views.PersonaListView.as_view(), name='persona-list'),
    path('personas/generate/', views.GeneratePersonasView.as_view(), name='persona-generate'),
    path('personas/<uuid:pk>/', views.PersonaDetailView.as_view(), name='persona-detail'),

    # One-pagers
    path('one-pagers/', views.OnePagerListView.as_view(), name='one-pager-list'),
    path('one-pagers/generate/', views.GenerateOnePagerView.as_view(), name='one-pager-generate'),
    path('one-pagers/<uuid:pk>/', views.OnePagerDetailView.as_view(), name='one-pager-detail'),
    path('one-pagers/<uuid:pk>/html/', views.OnePagerHtmlView.as_view(), name='one-pager-html'),

    # Account plans
    path('account-plans/generate/', views.GenerateAccountPlanView.as_view(), name='account-plan-generate'),
    path('account-plans/<uuid:pk>/', views.AccountPlanDetailView.as_view(), name='account-plan-detail'),
    path('account-plans/<uuid:pk>/html/', views.AccountPlanHtmlView.as_view(), name='account-plan-html'),

    # Citations
    path('citations/', views.CitationListView.as_view(), name='citation-list'),
    path('citations/<uuid:pk>/', views.CitationDetailView.as_view(), name='citation-detail'),
]
