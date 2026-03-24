"""Tests for ExportService — HTML generation for OnePager and AccountPlan."""
import pytest
from unittest.mock import patch, MagicMock

from research.models import ResearchJob
from assets.models import OnePager, AccountPlan
from assets.services.export import ExportService


@pytest.fixture
def research_job(db):
    return ResearchJob.objects.create(
        client_name="Acme Corp",
        sales_history="",
        status="completed",
        result="",
    )


@pytest.fixture
def one_pager(db, research_job):
    return OnePager.objects.create(
        research_job=research_job,
        title="Acme One-Pager",
        headline="Smarter Operations with AI",
        executive_summary="Acme can reduce costs by 30% with AI.",
        challenge_section="Legacy systems slowing them down.",
        solution_section="Our platform integrates seamlessly.",
        benefits_section="Faster, cheaper, more reliable.",
        differentiators=["SOC2 certified", "24/7 support"],
        call_to_action="Book a demo today",
        next_steps=["Schedule discovery call", "POC in 2 weeks"],
    )


@pytest.fixture
def account_plan(db, research_job):
    return AccountPlan.objects.create(
        research_job=research_job,
        title="Acme Account Plan",
        executive_summary="Strategic roadmap for Acme.",
        account_overview="Acme Corp is a mid-market manufacturer.",
        strategic_objectives=["Reduce TCO", "Accelerate AI adoption"],
        key_stakeholders=[
            {"name": "Jane Doe", "title": "CIO", "role_in_decision": "Approver", "engagement_approach": "Executive briefing"}
        ],
        opportunities=[
            {"name": "Cloud migration", "value": "$500k", "timeline": "Q3", "probability": "High"}
        ],
        swot_analysis={
            "strengths": ["Market leader"],
            "weaknesses": ["Legacy tech"],
            "opportunities": ["AI adoption"],
            "threats": ["New competitors"],
        },
        engagement_strategy="Lead with AI ROI story.",
        action_plan=[
            {"action": "Intro call", "owner": "AE", "due_date": "2026-04-01", "status": "pending"}
        ],
        success_metrics=["25% cost reduction", "90-day POC complete"],
        timeline="6 months to full deployment",
    )


@pytest.mark.django_db
class TestGenerateOnePagerHtml:
    """Tests for ExportService.generate_one_pager_html()."""

    def test_returns_html_string(self, one_pager):
        service = ExportService()
        result = service.generate_one_pager_html(one_pager)
        assert isinstance(result, str)
        assert result.startswith('<!DOCTYPE html>') or '<!DOCTYPE html>' in result

    def test_html_contains_title(self, one_pager):
        service = ExportService()
        result = service.generate_one_pager_html(one_pager)
        assert "Acme One-Pager" in result

    def test_html_contains_headline(self, one_pager):
        service = ExportService()
        result = service.generate_one_pager_html(one_pager)
        assert "Smarter Operations with AI" in result

    def test_html_contains_differentiators(self, one_pager):
        service = ExportService()
        result = service.generate_one_pager_html(one_pager)
        assert "SOC2 certified" in result
        assert "24/7 support" in result

    def test_html_contains_next_steps(self, one_pager):
        service = ExportService()
        result = service.generate_one_pager_html(one_pager)
        assert "Schedule discovery call" in result
        assert "POC in 2 weeks" in result

    def test_xss_characters_are_escaped(self, research_job):
        """LLM-generated content with XSS payloads is escaped."""
        pager = OnePager.objects.create(
            research_job=research_job,
            title='<script>alert("xss")</script>',
            headline="Safe headline",
            executive_summary="<b>bold</b>",
            challenge_section="Normal",
            solution_section="Normal",
            benefits_section="Normal",
        )
        service = ExportService()
        result = service.generate_one_pager_html(pager)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_html_content_saved_to_model(self, one_pager):
        """generate_one_pager_html saves HTML back to html_content field."""
        service = ExportService()
        result = service.generate_one_pager_html(one_pager)
        one_pager.refresh_from_db()
        assert one_pager.html_content == result

    def test_empty_lists_render_without_error(self, research_job):
        """One-pager with empty differentiators/next_steps renders cleanly."""
        pager = OnePager.objects.create(
            research_job=research_job,
            title="Minimal Pager",
            headline="Headline",
            executive_summary="Summary",
            challenge_section="Challenge",
            solution_section="Solution",
            benefits_section="Benefits",
            differentiators=[],
            next_steps=[],
        )
        service = ExportService()
        result = service.generate_one_pager_html(pager)
        assert "Minimal Pager" in result


@pytest.mark.django_db
class TestGenerateAccountPlanHtml:
    """Tests for ExportService.generate_account_plan_html()."""

    def test_returns_html_string(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result

    def test_html_contains_title(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert "Acme Account Plan" in result

    def test_html_contains_executive_summary(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert "Strategic roadmap for Acme" in result

    def test_html_contains_strategic_objectives(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert "Reduce TCO" in result
        assert "Accelerate AI adoption" in result

    def test_html_contains_stakeholders_table(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert "Jane Doe" in result
        assert "Executive briefing" in result

    def test_html_contains_opportunities_table(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert "Cloud migration" in result
        assert "$500k" in result

    def test_html_contains_swot_analysis(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert "Market leader" in result
        assert "Legacy tech" in result
        assert "AI adoption" in result
        assert "New competitors" in result

    def test_html_contains_action_plan(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert "Intro call" in result

    def test_html_contains_success_metrics(self, account_plan):
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        assert "25% cost reduction" in result

    def test_xss_characters_are_escaped(self, research_job):
        """XSS in stakeholder names is escaped."""
        plan = AccountPlan.objects.create(
            research_job=research_job,
            title='<img src=x onerror=alert(1)>',
            executive_summary="Safe summary",
            account_overview="Safe overview",
            key_stakeholders=[
                {"name": "<script>bad</script>", "title": "CTO", "role_in_decision": "", "engagement_approach": ""}
            ],
        )
        service = ExportService()
        result = service.generate_account_plan_html(plan)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_html_saved_to_model(self, account_plan):
        """generate_account_plan_html saves HTML back to html_content field."""
        service = ExportService()
        result = service.generate_account_plan_html(account_plan)
        account_plan.refresh_from_db()
        assert account_plan.html_content == result

    def test_empty_stakeholders_shows_no_stakeholders_message(self, research_job):
        """Empty stakeholders list renders 'No stakeholders identified'."""
        plan = AccountPlan.objects.create(
            research_job=research_job,
            title="Minimal Plan",
            executive_summary="Summary",
            account_overview="Overview",
            key_stakeholders=[],
            opportunities=[],
        )
        service = ExportService()
        result = service.generate_account_plan_html(plan)
        assert "No stakeholders identified" in result

    def test_empty_opportunities_shows_no_opportunities_message(self, research_job):
        plan = AccountPlan.objects.create(
            research_job=research_job,
            title="Min Plan 2",
            executive_summary="Summary",
            account_overview="Overview",
            opportunities=[],
        )
        service = ExportService()
        result = service.generate_account_plan_html(plan)
        assert "No opportunities identified" in result


@pytest.mark.django_db
class TestExportToPdf:
    """Tests for ExportService.export_to_pdf() — failure/fallback paths."""

    def test_returns_none_when_weasyprint_not_installed(self):
        service = ExportService()
        with patch.dict("sys.modules", {"weasyprint": None}):
            result = service.export_to_pdf("<html></html>", "test.pdf")
        assert result is None

    def test_returns_none_on_exception(self, tmp_path):
        service = ExportService()
        with patch("assets.services.export.settings") as mock_settings:
            mock_settings.BASE_DIR = str(tmp_path)
            with patch("assets.services.export.os.makedirs"):
                with patch("builtins.__import__", side_effect=ImportError("weasyprint")):
                    result = service.export_to_pdf("<html></html>", "test.pdf")
        assert result is None
