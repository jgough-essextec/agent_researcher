from typing import Optional, TypedDict


class OsintState(TypedDict):
    # Identifiers
    job_id: str
    organization_name: str
    primary_domain: str
    additional_domains: list[str]
    engagement_context: str

    # Optional link to prior research
    research_job_id: Optional[str]
    prior_research_context: Optional[dict]

    # Lifecycle
    status: str
    error: str
    warnings: list[str]

    # Phase 1 outputs
    web_research: Optional[dict]
    breach_history: Optional[list]
    job_postings_intel: Optional[dict]
    regulatory_framework: Optional[dict]
    vendor_relationships: Optional[list]
    leadership_intel: Optional[list]

    # Phase 2 outputs — automated
    crt_sh_subdomains: Optional[list]
    dns_records: Optional[list]
    email_security: Optional[dict]
    whois_data: Optional[dict]
    arin_data: Optional[list]

    # Phase 2 outputs — user-submitted terminal
    terminal_submissions: Optional[list]

    # Phase 3 outputs
    screenshots: Optional[list]
    screenshot_analyses: Optional[list]

    # Phase 4 outputs
    infrastructure_map: Optional[dict]
    technology_stack: Optional[dict]
    risk_matrix: Optional[dict]
    severity_table: Optional[list]

    # Phase 5 outputs
    report_sections: Optional[dict]
    service_mappings: Optional[list]
    report_file_path: Optional[str]
