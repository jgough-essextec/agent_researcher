"""Constants and enums for the research module."""
from enum import Enum


class Vertical(str, Enum):
    """Industry vertical taxonomy for client classification."""

    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    TECHNOLOGY = "technology"
    ENERGY = "energy"
    TELECOMMUNICATIONS = "telecommunications"
    MEDIA_ENTERTAINMENT = "media_entertainment"
    TRANSPORTATION = "transportation"
    REAL_ESTATE = "real_estate"
    PROFESSIONAL_SERVICES = "professional_services"
    EDUCATION = "education"
    GOVERNMENT = "government"
    HOSPITALITY = "hospitality"
    AGRICULTURE = "agriculture"
    CONSTRUCTION = "construction"
    NONPROFIT = "nonprofit"
    OTHER = "other"

    @classmethod
    def choices(cls):
        """Return choices tuple for Django model fields."""
        return [(v.value, v.name.replace('_', ' ').title()) for v in cls]


class DigitalMaturityLevel(str, Enum):
    """Digital maturity assessment levels."""

    NASCENT = "nascent"
    DEVELOPING = "developing"
    MATURING = "maturing"
    ADVANCED = "advanced"
    LEADING = "leading"

    @classmethod
    def choices(cls):
        """Return choices tuple for Django model fields."""
        return [(v.value, v.name.title()) for v in cls]


class AIAdoptionStage(str, Enum):
    """AI adoption stage classification."""

    EXPLORING = "exploring"
    EXPERIMENTING = "experimenting"
    IMPLEMENTING = "implementing"
    SCALING = "scaling"
    OPTIMIZING = "optimizing"

    @classmethod
    def choices(cls):
        """Return choices tuple for Django model fields."""
        return [(v.value, v.name.title()) for v in cls]
