from django.urls import path
from . import views

urlpatterns = [
    path('', views.ResearchJobCreateView.as_view(), name='research-create'),
    path('<uuid:pk>/', views.ResearchJobDetailView.as_view(), name='research-detail'),
]
