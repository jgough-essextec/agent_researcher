"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('api/research/', include('research.urls')),
    path('api/prompts/', include('prompts.urls')),
    path('api/memory/', include('memory.urls')),
    path('api/ideation/', include('ideation.urls')),
    path('api/assets/', include('assets.urls')),
    path('api/projects/', include('projects.urls')),
]
