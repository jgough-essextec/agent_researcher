from docx import Document
from osint.models import OsintJob, OsintReportSection


class BaseReportSection:
    def __init__(self, osint_job: OsintJob, db_section: OsintReportSection | None = None):
        self.job = osint_job
        self.db_section = db_section

    def render(self, document: Document) -> None:
        raise NotImplementedError
