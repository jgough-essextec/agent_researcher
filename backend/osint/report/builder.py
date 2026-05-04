import os
from docx import Document
from docx.shared import Pt
from django.conf import settings
from osint.models import OsintJob, OsintReportSection
from .sections.base import BaseReportSection
from .sections.cover import CoverSection
from .sections.generic import GenericSection
from .sections.infrastructure_maps import InfrastructureMapsSection

SECTION_ORDER = [
    'cover',
    'executive_summary',
    'remediation_plan',
    'security_roadmap',
    'entity_findings',
    'regulatory_landscape',
    'engagement_proposal',
    'methodology',
    'infrastructure_maps',
]


class OsintReportBuilder:
    """Builds the complete OSINT .docx report."""

    def __init__(self, osint_job: OsintJob):
        self.job = osint_job
        self.document = Document()
        self._sections: list[BaseReportSection] = []
        self._apply_global_styles()

    def _apply_global_styles(self) -> None:
        style = self.document.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)

    def add_all_sections(self) -> 'OsintReportBuilder':
        db_sections = {
            s.section_type: s
            for s in OsintReportSection.objects.filter(osint_job=self.job).order_by('order')
        }

        self._sections = []
        for section_type in SECTION_ORDER:
            db_section = db_sections.get(section_type)
            if section_type == 'cover':
                self._sections.append(CoverSection(self.job, db_section))
            elif section_type == 'infrastructure_maps':
                self._sections.append(InfrastructureMapsSection(self.job, db_section))
            else:
                self._sections.append(GenericSection(self.job, db_section))

        return self

    def build(self) -> str:
        """Render all sections and write the .docx file. Returns the output file path."""
        for section in self._sections:
            section.render(self.document)

        output_path = self._get_output_path()
        self.document.save(output_path)
        return output_path

    def _get_output_path(self) -> str:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'osint_reports')
        os.makedirs(output_dir, exist_ok=True)
        safe_name = "".join(
            c if c.isalnum() or c == '_' else '_'
            for c in self.job.organization_name
        )
        return os.path.join(output_dir, f"OSINT_{safe_name}_{str(self.job.id)[:8]}.docx")
