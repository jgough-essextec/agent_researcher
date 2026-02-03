"""Export service for generating PDFs and HTML (AGE-24)."""
import logging
import os
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting assets to HTML and PDF."""

    ONE_PAGER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #333; }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0066cc; padding-bottom: 20px; }}
        .headline {{ font-size: 24px; color: #0066cc; margin-bottom: 10px; }}
        .summary {{ font-size: 14px; color: #666; line-height: 1.6; }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{ font-size: 16px; font-weight: bold; color: #0066cc; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }}
        .section-content {{ font-size: 14px; line-height: 1.6; }}
        .differentiators {{ list-style: none; padding: 0; }}
        .differentiators li {{ padding: 8px 0 8px 25px; position: relative; }}
        .differentiators li:before {{ content: "✓"; position: absolute; left: 0; color: #0066cc; font-weight: bold; }}
        .cta {{ background: #0066cc; color: white; padding: 15px 25px; border-radius: 5px; text-align: center; margin-top: 30px; }}
        .next-steps {{ margin-top: 15px; }}
        .next-steps li {{ margin-bottom: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="headline">{headline}</div>
    </div>

    <div class="section">
        <div class="summary">{executive_summary}</div>
    </div>

    <div class="section">
        <div class="section-title">The Challenge</div>
        <div class="section-content">{challenge_section}</div>
    </div>

    <div class="section">
        <div class="section-title">Our Solution</div>
        <div class="section-content">{solution_section}</div>
    </div>

    <div class="section">
        <div class="section-title">Key Benefits</div>
        <div class="section-content">{benefits_section}</div>
    </div>

    <div class="section">
        <div class="section-title">Why Choose Us</div>
        <ul class="differentiators">
            {differentiators_html}
        </ul>
    </div>

    <div class="cta">{call_to_action}</div>

    <div class="section next-steps">
        <div class="section-title">Next Steps</div>
        <ol>
            {next_steps_html}
        </ol>
    </div>
</body>
</html>
'''

    ACCOUNT_PLAN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; color: #333; }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 3px solid #0066cc; padding-bottom: 20px; }}
        h1 {{ color: #0066cc; }}
        .executive-summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
        .section {{ margin-bottom: 30px; page-break-inside: avoid; }}
        .section-title {{ font-size: 18px; font-weight: bold; color: #0066cc; margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        .section-content {{ font-size: 14px; line-height: 1.6; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 13px; }}
        th {{ background: #0066cc; color: white; }}
        .swot {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
        .swot-box {{ padding: 15px; border-radius: 5px; }}
        .strengths {{ background: #e8f5e9; }}
        .weaknesses {{ background: #ffebee; }}
        .opportunities {{ background: #e3f2fd; }}
        .threats {{ background: #fff3e0; }}
        .swot-title {{ font-weight: bold; margin-bottom: 10px; }}
        ul {{ margin: 0; padding-left: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
    </div>

    <div class="executive-summary">
        <h2>Executive Summary</h2>
        <p>{executive_summary}</p>
    </div>

    <div class="section">
        <div class="section-title">Account Overview</div>
        <div class="section-content">{account_overview}</div>
    </div>

    <div class="section">
        <div class="section-title">Strategic Objectives</div>
        <ul>
            {strategic_objectives_html}
        </ul>
    </div>

    <div class="section">
        <div class="section-title">Key Stakeholders</div>
        {stakeholders_table}
    </div>

    <div class="section">
        <div class="section-title">Opportunities</div>
        {opportunities_table}
    </div>

    <div class="section">
        <div class="section-title">SWOT Analysis</div>
        <div class="swot">
            <div class="swot-box strengths">
                <div class="swot-title">Strengths</div>
                <ul>{swot_strengths}</ul>
            </div>
            <div class="swot-box weaknesses">
                <div class="swot-title">Weaknesses</div>
                <ul>{swot_weaknesses}</ul>
            </div>
            <div class="swot-box opportunities">
                <div class="swot-title">Opportunities</div>
                <ul>{swot_opportunities}</ul>
            </div>
            <div class="swot-box threats">
                <div class="swot-title">Threats</div>
                <ul>{swot_threats}</ul>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Engagement Strategy</div>
        <div class="section-content">{engagement_strategy}</div>
    </div>

    <div class="section">
        <div class="section-title">Action Plan</div>
        {action_plan_table}
    </div>

    <div class="section">
        <div class="section-title">Success Metrics</div>
        <ul>
            {success_metrics_html}
        </ul>
    </div>

    <div class="section">
        <div class="section-title">Timeline</div>
        <div class="section-content">{timeline}</div>
    </div>
</body>
</html>
'''

    def generate_one_pager_html(self, one_pager) -> str:
        """Generate HTML for a one-pager.

        Args:
            one_pager: OnePager model instance

        Returns:
            HTML string
        """
        differentiators_html = '\n'.join([f'<li>{d}</li>' for d in (one_pager.differentiators or [])])
        next_steps_html = '\n'.join([f'<li>{s}</li>' for s in (one_pager.next_steps or [])])

        html = self.ONE_PAGER_TEMPLATE.format(
            title=one_pager.title,
            headline=one_pager.headline,
            executive_summary=one_pager.executive_summary,
            challenge_section=one_pager.challenge_section,
            solution_section=one_pager.solution_section,
            benefits_section=one_pager.benefits_section,
            differentiators_html=differentiators_html,
            call_to_action=one_pager.call_to_action,
            next_steps_html=next_steps_html,
        )

        # Save HTML to model
        one_pager.html_content = html
        one_pager.save(update_fields=['html_content'])

        return html

    def generate_account_plan_html(self, account_plan) -> str:
        """Generate HTML for an account plan.

        Args:
            account_plan: AccountPlan model instance

        Returns:
            HTML string
        """
        # Strategic objectives
        strategic_objectives_html = '\n'.join([f'<li>{o}</li>' for o in (account_plan.strategic_objectives or [])])

        # Stakeholders table
        stakeholders = account_plan.key_stakeholders or []
        stakeholders_rows = '\n'.join([
            f"<tr><td>{s.get('name', '')}</td><td>{s.get('title', '')}</td><td>{s.get('role_in_decision', '')}</td><td>{s.get('engagement_approach', '')}</td></tr>"
            for s in stakeholders
        ])
        stakeholders_table = f'''
        <table>
            <tr><th>Name</th><th>Title</th><th>Role</th><th>Engagement Approach</th></tr>
            {stakeholders_rows}
        </table>
        ''' if stakeholders_rows else '<p>No stakeholders identified</p>'

        # Opportunities table
        opportunities = account_plan.opportunities or []
        opportunities_rows = '\n'.join([
            f"<tr><td>{o.get('name', '')}</td><td>{o.get('value', '')}</td><td>{o.get('timeline', '')}</td><td>{o.get('probability', '')}</td></tr>"
            for o in opportunities
        ])
        opportunities_table = f'''
        <table>
            <tr><th>Opportunity</th><th>Value</th><th>Timeline</th><th>Probability</th></tr>
            {opportunities_rows}
        </table>
        ''' if opportunities_rows else '<p>No opportunities identified</p>'

        # SWOT
        swot = account_plan.swot_analysis or {}
        swot_strengths = '\n'.join([f'<li>{s}</li>' for s in swot.get('strengths', [])])
        swot_weaknesses = '\n'.join([f'<li>{w}</li>' for w in swot.get('weaknesses', [])])
        swot_opportunities = '\n'.join([f'<li>{o}</li>' for o in swot.get('opportunities', [])])
        swot_threats = '\n'.join([f'<li>{t}</li>' for t in swot.get('threats', [])])

        # Action plan table
        actions = account_plan.action_plan or []
        action_rows = '\n'.join([
            f"<tr><td>{a.get('action', '')}</td><td>{a.get('owner', '')}</td><td>{a.get('due_date', '')}</td><td>{a.get('status', '')}</td></tr>"
            for a in actions
        ])
        action_plan_table = f'''
        <table>
            <tr><th>Action</th><th>Owner</th><th>Due Date</th><th>Status</th></tr>
            {action_rows}
        </table>
        ''' if action_rows else '<p>No actions defined</p>'

        # Success metrics
        success_metrics_html = '\n'.join([f'<li>{m}</li>' for m in (account_plan.success_metrics or [])])

        html = self.ACCOUNT_PLAN_TEMPLATE.format(
            title=account_plan.title,
            executive_summary=account_plan.executive_summary,
            account_overview=account_plan.account_overview,
            strategic_objectives_html=strategic_objectives_html,
            stakeholders_table=stakeholders_table,
            opportunities_table=opportunities_table,
            swot_strengths=swot_strengths,
            swot_weaknesses=swot_weaknesses,
            swot_opportunities=swot_opportunities,
            swot_threats=swot_threats,
            engagement_strategy=account_plan.engagement_strategy,
            action_plan_table=action_plan_table,
            success_metrics_html=success_metrics_html,
            timeline=account_plan.timeline,
        )

        # Save HTML to model
        account_plan.html_content = html
        account_plan.save(update_fields=['html_content'])

        return html

    def export_to_pdf(self, html_content: str, output_filename: str) -> Optional[str]:
        """Export HTML to PDF using weasyprint.

        Args:
            html_content: HTML string to convert
            output_filename: Name of the output file

        Returns:
            Path to the generated PDF, or None if failed
        """
        try:
            from weasyprint import HTML

            # Ensure export directory exists
            export_dir = os.path.join(settings.BASE_DIR, 'exports')
            os.makedirs(export_dir, exist_ok=True)

            output_path = os.path.join(export_dir, output_filename)
            HTML(string=html_content).write_pdf(output_path)

            logger.info(f"Generated PDF: {output_path}")
            return output_path

        except ImportError:
            logger.warning("weasyprint not installed, skipping PDF export")
            return None
        except Exception as e:
            logger.exception(f"Failed to generate PDF: {e}")
            return None
