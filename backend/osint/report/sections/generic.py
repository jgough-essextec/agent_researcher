from docx import Document
from .base import BaseReportSection


class GenericSection(BaseReportSection):
    """Renders a report section as a heading + body text paragraphs."""

    def __init__(self, osint_job, db_section=None, heading_level: int = 1):
        super().__init__(osint_job, db_section)
        self.heading_level = heading_level

    def render(self, document: Document) -> None:
        document.add_page_break()
        title = self.db_section.title if self.db_section else self._default_title()
        document.add_heading(title, level=self.heading_level)

        content = self.db_section.content if self.db_section else "(Content not yet generated)"
        for paragraph in content.split('\n\n'):
            paragraph = paragraph.strip()
            if paragraph:
                document.add_paragraph(paragraph)

    def _default_title(self) -> str:
        return "Section"
