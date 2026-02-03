"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/research/', include('research.urls')),
    path('api/prompts/', include('prompts.urls')),
    path('api/memory/', include('memory.urls')),
    path('api/ideation/', include('ideation.urls')),
    path('api/assets/', include('assets.urls')),
]
