from django.urls import path
from . import views

urlpatterns = [
    path('default/', views.DefaultPromptView.as_view(), name='prompt-default'),
]
