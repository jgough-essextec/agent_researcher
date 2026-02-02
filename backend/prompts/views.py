from rest_framework import generics
from rest_framework.response import Response
from .models import PromptTemplate
from .serializers import PromptTemplateSerializer


class DefaultPromptView(generics.RetrieveUpdateAPIView):
    """View for getting and updating the default prompt template."""

    serializer_class = PromptTemplateSerializer

    def get_object(self):
        return PromptTemplate.get_default()
