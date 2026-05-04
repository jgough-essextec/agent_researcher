"""Tests for _parse_ops_data null-safety (Bug 2 regression tests)."""
import pytest


class TestParseOpsDataNullSafety:
    """All these tests verify the or-default pattern handles explicit null values."""

    def _make_service(self):
        from unittest.mock import MagicMock
        from research.services.internal_ops import InternalOpsService
        svc = InternalOpsService.__new__(InternalOpsService)
        svc.gemini_client = MagicMock()
        return svc

    def test_null_positive_themes_becomes_empty_list(self):
        svc = self._make_service()
        data = {"employee_sentiment": {"overall_rating": 3.5, "positive_themes": None}}
        result = svc._parse_ops_data(data)
        assert result.employee_sentiment.positive_themes == []

    def test_null_negative_themes_becomes_empty_list(self):
        svc = self._make_service()
        data = {"employee_sentiment": {"negative_themes": None}}
        result = svc._parse_ops_data(data)
        assert result.employee_sentiment.negative_themes == []

    def test_null_recent_posts_becomes_empty_list(self):
        svc = self._make_service()
        data = {"linkedin_presence": {"recent_posts": None}}
        result = svc._parse_ops_data(data)
        assert result.linkedin_presence.recent_posts == []

    def test_null_notable_changes_becomes_empty_list(self):
        svc = self._make_service()
        data = {"linkedin_presence": {"notable_changes": None}}
        result = svc._parse_ops_data(data)
        assert result.linkedin_presence.notable_changes == []

    def test_null_departments_hiring_becomes_empty_dict(self):
        svc = self._make_service()
        data = {"job_postings": {"departments_hiring": None}}
        result = svc._parse_ops_data(data)
        assert result.job_postings.departments_hiring == {}

    def test_null_skills_sought_becomes_empty_list(self):
        svc = self._make_service()
        data = {"job_postings": {"skills_sought": None}}
        result = svc._parse_ops_data(data)
        assert result.job_postings.skills_sought == []

    def test_null_seniority_distribution_becomes_empty_dict(self):
        svc = self._make_service()
        data = {"job_postings": {"seniority_distribution": None}}
        result = svc._parse_ops_data(data)
        assert result.job_postings.seniority_distribution == {}

    def test_null_urgency_signals_becomes_empty_list(self):
        svc = self._make_service()
        data = {"job_postings": {"urgency_signals": None}}
        result = svc._parse_ops_data(data)
        assert result.job_postings.urgency_signals == []

    def test_null_news_topics_becomes_empty_list(self):
        svc = self._make_service()
        data = {"news_sentiment": {"topics": None}}
        result = svc._parse_ops_data(data)
        assert result.news_sentiment.topics == []

    def test_null_headlines_becomes_empty_list(self):
        svc = self._make_service()
        data = {"news_sentiment": {"headlines": None}}
        result = svc._parse_ops_data(data)
        assert result.news_sentiment.headlines == []

    def test_null_key_insights_becomes_empty_list(self):
        svc = self._make_service()
        data = {"key_insights": None}
        result = svc._parse_ops_data(data)
        assert result.key_insights == []

    def test_null_social_media_mentions_becomes_empty_list(self):
        svc = self._make_service()
        data = {"social_media_mentions": None}
        result = svc._parse_ops_data(data)
        assert result.social_media_mentions == []

    def test_top_level_null_employee_sentiment_uses_defaults(self):
        """If employee_sentiment key exists but is null, use defaults."""
        svc = self._make_service()
        data = {"employee_sentiment": None}
        result = svc._parse_ops_data(data)
        assert result.employee_sentiment.overall_rating == 0.0
        assert result.employee_sentiment.positive_themes == []

    def test_top_level_null_job_postings_uses_defaults(self):
        svc = self._make_service()
        data = {"job_postings": None}
        result = svc._parse_ops_data(data)
        assert result.job_postings.departments_hiring == {}
        assert result.job_postings.skills_sought == []

    def test_entirely_empty_dict_uses_all_defaults(self):
        svc = self._make_service()
        result = svc._parse_ops_data({})
        assert result.employee_sentiment.overall_rating == 0.0
        assert result.job_postings.total_openings == 0
        assert result.linkedin_presence.follower_count == 0

    def test_valid_data_preserved(self):
        """Existing valid data is not changed by the fix."""
        svc = self._make_service()
        data = {
            "employee_sentiment": {
                "overall_rating": 4.2,
                "positive_themes": ["Great culture", "Smart people"],
                "negative_themes": ["Long hours"],
                "trend": "improving"
            }
        }
        result = svc._parse_ops_data(data)
        assert result.employee_sentiment.overall_rating == 4.2
        assert result.employee_sentiment.positive_themes == ["Great culture", "Smart people"]
        assert result.employee_sentiment.negative_themes == ["Long hours"]
        assert result.employee_sentiment.trend == "improving"
