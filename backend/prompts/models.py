from django.db import models


class PromptTemplate(models.Model):
    """Model to store prompt templates."""

    name = models.CharField(max_length=100, unique=True)
    content = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-updated_at']

    def __str__(self):
        return f"{self.name} {'(default)' if self.is_default else ''}"

    def save(self, *args, **kwargs):
        # Ensure only one default prompt exists
        if self.is_default:
            PromptTemplate.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls):
        """Get the default prompt template, creating one if it doesn't exist."""
        prompt, created = cls.objects.get_or_create(
            is_default=True,
            defaults={
                'name': 'default',
                'content': cls.get_default_content(),
            }
        )
        return prompt

    @staticmethod
    def get_default_content():
        return """You are a deep research assistant helping with prospect research.

Given the following client information:
- Client Name: {client_name}
- Past Sales History: {sales_history}

Please conduct comprehensive research on this prospect and provide:
1. Company overview and recent news
2. Key decision makers and their backgrounds
3. Potential pain points and challenges
4. Opportunities for engagement
5. Recommended talking points for sales outreach

Be thorough and provide actionable insights."""
