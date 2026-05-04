import uuid
from django.db import models


class OsintJob(models.Model):
    """Top-level OSINT investigation entity."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('phase1_research', 'Phase 1: Web Research'),
        ('phase1_complete', 'Phase 1 Complete'),
        ('phase2_auto', 'Phase 2: Automated DNS'),
        ('awaiting_terminal_output', 'Awaiting Terminal Output'),
        ('phase2_processing', 'Phase 2: Processing DNS'),
        ('awaiting_screenshots', 'Awaiting Screenshots'),
        ('phase3_processing', 'Phase 3: Processing Screenshots'),
        ('phase4_analysis', 'Phase 4: Analysis'),
        ('phase5_report', 'Phase 5: Report Generation'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    research_job = models.ForeignKey(
        'research.ResearchJob',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='osint_jobs',
    )
    organization_name = models.CharField(max_length=255)
    primary_domain = models.CharField(max_length=255)
    additional_domains = models.JSONField(default=list)
    engagement_context = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    current_step = models.CharField(max_length=200, blank=True)
    error = models.TextField(blank=True)

    # Phase completion timestamps
    phase1_completed_at = models.DateTimeField(null=True, blank=True)
    phase2_completed_at = models.DateTimeField(null=True, blank=True)
    phase3_completed_at = models.DateTimeField(null=True, blank=True)
    phase4_completed_at = models.DateTimeField(null=True, blank=True)
    phase5_completed_at = models.DateTimeField(null=True, blank=True)

    report_file = models.FileField(upload_to='osint_reports/', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.organization_name} ({self.primary_domain}) — {self.status}"


class DnsFinding(models.Model):
    """DNS record finding for an OSINT job."""

    RECORD_TYPE_CHOICES = [
        ('MX', 'MX'),
        ('TXT', 'TXT'),
        ('NS', 'NS'),
        ('A', 'A'),
        ('AAAA', 'AAAA'),
        ('CNAME', 'CNAME'),
        ('SOA', 'SOA'),
        ('DMARC', 'DMARC'),
        ('SPF', 'SPF'),
        ('PTR', 'PTR'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='dns_findings',
    )
    domain = models.CharField(max_length=255)
    record_type = models.CharField(max_length=10, choices=RECORD_TYPE_CHOICES)
    record_value = models.TextField()
    analysis = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, blank=True)

    def __str__(self) -> str:
        return f"{self.record_type} {self.domain}"


class SubdomainFinding(models.Model):
    """Subdomain discovery finding for an OSINT job."""

    CATEGORY_CHOICES = [
        ('production', 'Production'),
        ('staging', 'Staging'),
        ('dev', 'Development'),
        ('vpn', 'VPN'),
        ('mail', 'Mail'),
        ('admin', 'Admin'),
        ('api', 'API'),
        ('cdn', 'CDN'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='subdomain_findings',
    )
    subdomain = models.CharField(max_length=500)
    source = models.CharField(max_length=50)
    resolves_to = models.GenericIPAddressField(null=True, blank=True)
    is_alive = models.BooleanField(null=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='unknown')
    risk_notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.subdomain} ({self.category})"


class InfrastructureFinding(models.Model):
    """Cloud/infrastructure provider finding for an OSINT job."""

    INFRA_TYPE_CHOICES = [
        ('cloud_provider', 'Cloud Provider'),
        ('cdn', 'CDN'),
        ('data_center', 'Data Center'),
        ('colo', 'Colocation'),
        ('isp', 'ISP'),
        ('vpn_gateway', 'VPN Gateway'),
        ('email_provider', 'Email Provider'),
        ('dns_provider', 'DNS Provider'),
        ('waf', 'WAF'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='infra_findings',
    )
    infra_type = models.CharField(max_length=30, choices=INFRA_TYPE_CHOICES)
    provider_name = models.CharField(max_length=255)
    evidence = models.TextField()
    ip_ranges = models.JSONField(default=list)
    associated_domains = models.JSONField(default=list)
    confidence = models.FloatField(default=0.0)
    risk_notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.infra_type}: {self.provider_name}"


class WhoisRecord(models.Model):
    """WHOIS registration record for a domain."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='whois_records',
    )
    domain = models.CharField(max_length=255)
    registrant_name = models.CharField(max_length=255, blank=True)
    registrant_org = models.CharField(max_length=255, blank=True)
    registrar = models.CharField(max_length=255, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    name_servers = models.JSONField(default=list)
    raw_whois = models.TextField(blank=True)
    risk_notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"WHOIS: {self.domain}"


class EmailSecurityAssessment(models.Model):
    """Email security posture assessment for a domain."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='email_assessments',
    )
    domain = models.CharField(max_length=255)
    has_spf = models.BooleanField(default=False)
    spf_record = models.TextField(blank=True)
    spf_assessment = models.CharField(max_length=50, blank=True)
    has_dkim = models.BooleanField(null=True)
    has_dmarc = models.BooleanField(default=False)
    dmarc_record = models.TextField(blank=True)
    dmarc_policy = models.CharField(max_length=20, blank=True)
    mx_providers = models.JSONField(default=list)
    overall_grade = models.CharField(max_length=5, blank=True)
    risk_summary = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Email Security: {self.domain} (grade: {self.overall_grade or 'ungraded'})"


class ScreenshotUpload(models.Model):
    """Screenshot uploaded by the analyst during phase 3."""

    SOURCE_CHOICES = [
        ('dnsdumpster', 'DNSDumpster'),
        ('shodan', 'Shodan'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='screenshots',
    )
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    image = models.ImageField(upload_to='osint_screenshots/')
    caption = models.CharField(max_length=500, blank=True)
    analysis = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"Screenshot [{self.source}] for {self.osint_job.organization_name}"


class TerminalSubmission(models.Model):
    """Terminal command output submitted by the analyst."""

    COMMAND_TYPE_CHOICES = [
        ('dig', 'dig'),
        ('whois', 'whois'),
        ('curl', 'curl'),
        ('nslookup', 'nslookup'),
        ('arin', 'ARIN'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='terminal_submissions',
    )
    command_type = models.CharField(max_length=20, choices=COMMAND_TYPE_CHOICES)
    command_text = models.TextField()
    output_text = models.TextField()
    parsed_data = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"{self.command_type} submission for {self.osint_job.organization_name}"


class OsintCommandRound(models.Model):
    """A round of AI-suggested terminal commands for the analyst to run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='command_rounds',
    )
    round_number = models.PositiveIntegerField(default=1)
    commands = models.JSONField(default=list)
    rationale = models.TextField(blank=True)
    output_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['round_number']
        unique_together = ['osint_job', 'round_number']

    def __str__(self) -> str:
        return f"Round {self.round_number} for {self.osint_job.organization_name}"


class OsintReportSection(models.Model):
    """A generated section of the final OSINT report."""

    SECTION_TYPE_CHOICES = [
        ('cover', 'Cover'),
        ('executive_summary', 'Executive Summary'),
        ('remediation_plan', 'Remediation Plan'),
        ('security_roadmap', 'Security Roadmap'),
        ('entity_findings', 'Entity Findings'),
        ('regulatory_landscape', 'Regulatory Landscape'),
        ('engagement_proposal', 'Engagement Proposal'),
        ('methodology', 'Methodology'),
        ('infrastructure_maps', 'Infrastructure Maps'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='report_sections',
    )
    section_type = models.CharField(max_length=30, choices=SECTION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    structured_data = models.JSONField(default=dict)
    order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['osint_job', 'section_type']

    def __str__(self) -> str:
        return f"{self.section_type}: {self.title}"


class ServiceMapping(models.Model):
    """Mapping of OSINT findings to EssexTec service offerings."""

    SERVICE_CHOICES = [
        ('mdr_soc', 'MDR / SOC'),
        ('pen_test', 'Pen Test'),
        ('vciso_grc', 'vCISO / GRC'),
        ('ir_retainer', 'IR Retainer'),
        ('infrastructure', 'Infrastructure'),
        ('digital_workplace', 'Digital Workplace'),
        ('app_modernization', 'App Modernization'),
        ('ai_ops', 'AI Ops'),
        ('field_cto', 'Field CTO'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(
        OsintJob,
        on_delete=models.CASCADE,
        related_name='service_mappings',
    )
    service = models.CharField(max_length=30, choices=SERVICE_CHOICES)
    finding_summary = models.TextField()
    urgency = models.CharField(max_length=20)
    justification = models.TextField()

    def __str__(self) -> str:
        return f"{self.service} mapping for {self.osint_job.organization_name}"
