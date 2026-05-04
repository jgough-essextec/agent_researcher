# Plan 01 — Django App, Models & Migrations

**Depends on:** Nothing (first plan)  
**Unlocks:** All subsequent plans

---

## Goal

Bootstrap the `osint` Django app with all models, migrations, admin registration, and serializer scaffolding. No business logic — just the data layer that every other plan builds on.

---

## TDD Approach

Write model tests first. Verify:
- All models can be created with valid data
- Status transitions are constrained (choices validation)
- FK relationships work (OsintJob → ResearchJob nullable)
- JSONField defaults are non-shared (immutability)
- Unique constraints hold (OsintReportSection unique_together)
- `__str__` methods return readable output

Run: `pytest osint/tests/test_models.py`

---

## Step 1 — Create the App

```bash
cd backend
python manage.py startapp osint
```

---

## Step 2 — Register in Settings

**File:** `backend/backend/settings/base.py`

Add to `INSTALLED_APPS`:
```python
'osint',
```

Add settings after existing DB config:
```python
SHODAN_API_KEY = env('SHODAN_API_KEY', default='')
MEDIA_ROOT = env('MEDIA_ROOT', default=str(BASE_DIR / 'media'))
MEDIA_URL = '/media/'
```

Add to `backend/backend/urls.py` (also configure media serving in dev):
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    ...
    path('api/osint/', include('osint.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Step 3 — Write Model Tests First (TDD — RED)

**File:** `backend/osint/tests/test_models.py`

```python
import uuid
import pytest
from django.core.exceptions import ValidationError
from osint.models import (
    OsintJob, DnsFinding, SubdomainFinding, InfrastructureFinding,
    WhoisRecord, EmailSecurityAssessment, ScreenshotUpload,
    TerminalSubmission, OsintReportSection, ServiceMapping,
)


@pytest.mark.django_db
class TestOsintJob:
    def test_create_minimal(self):
        job = OsintJob.objects.create(
            organization_name="Acme Corp",
            primary_domain="acme.com",
        )
        assert job.id is not None
        assert job.status == 'pending'
        assert job.additional_domains == []
        assert job.research_job is None

    def test_str(self):
        job = OsintJob(organization_name="Acme", primary_domain="acme.com")
        assert "Acme" in str(job)
        assert "acme.com" in str(job)

    def test_additional_domains_defaults_empty_list(self):
        job1 = OsintJob.objects.create(organization_name="A", primary_domain="a.com")
        job2 = OsintJob.objects.create(organization_name="B", primary_domain="b.com")
        job1.additional_domains.append("extra.a.com")
        job1.save()
        job2.refresh_from_db()
        assert job2.additional_domains == []  # not shared mutable default

    def test_linked_research_job_nullable(self):
        job = OsintJob.objects.create(organization_name="X", primary_domain="x.com")
        assert job.research_job_id is None


@pytest.mark.django_db
class TestDnsFinding:
    def test_create(self, osint_job):
        finding = DnsFinding.objects.create(
            osint_job=osint_job,
            domain="acme.com",
            record_type="MX",
            record_value="10 mail.acme.com",
        )
        assert finding.id is not None
        assert finding.risk_level == ''


@pytest.mark.django_db
class TestEmailSecurityAssessment:
    def test_overall_grade_blank_by_default(self, osint_job):
        assessment = EmailSecurityAssessment.objects.create(
            osint_job=osint_job,
            domain="acme.com",
        )
        assert assessment.overall_grade == ''
        assert assessment.has_spf is False
        assert assessment.has_dmarc is False


@pytest.mark.django_db
class TestOsintReportSection:
    def test_unique_together(self, osint_job):
        OsintReportSection.objects.create(
            osint_job=osint_job,
            section_type='cover',
            title='Cover',
            content='...',
        )
        with pytest.raises(Exception):  # IntegrityError
            OsintReportSection.objects.create(
                osint_job=osint_job,
                section_type='cover',
                title='Cover 2',
                content='...',
            )
```

Add `conftest.py` with `osint_job` fixture:
```python
# backend/osint/tests/conftest.py
import pytest
from osint.models import OsintJob

@pytest.fixture
def osint_job(db):
    return OsintJob.objects.create(
        organization_name="Acme Corp",
        primary_domain="acme.com",
    )
```

---

## Step 4 — Implement Models (GREEN)

**File:** `backend/osint/models.py`

```python
import uuid
from django.db import models


class OsintJob(models.Model):
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
        null=True, blank=True,
        related_name='osint_jobs',
    )
    organization_name = models.CharField(max_length=255)
    primary_domain = models.CharField(max_length=255)
    additional_domains = models.JSONField(default=list, blank=True)
    engagement_context = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    current_step = models.CharField(max_length=200, blank=True)
    error = models.TextField(blank=True)
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

    def __str__(self):
        return f"{self.organization_name} ({self.primary_domain}) — {self.status}"


class DnsFinding(models.Model):
    RECORD_TYPES = [
        ('MX', 'MX'), ('TXT', 'TXT'), ('NS', 'NS'), ('A', 'A'),
        ('AAAA', 'AAAA'), ('CNAME', 'CNAME'), ('SOA', 'SOA'),
        ('DMARC', 'DMARC'), ('SPF', 'SPF'), ('PTR', 'PTR'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='dns_findings')
    domain = models.CharField(max_length=255)
    record_type = models.CharField(max_length=10, choices=RECORD_TYPES)
    record_value = models.TextField()
    analysis = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.record_type} {self.domain}: {self.record_value[:50]}"


class SubdomainFinding(models.Model):
    CATEGORIES = [
        ('production', 'Production'), ('staging', 'Staging'), ('dev', 'Development'),
        ('vpn', 'VPN'), ('mail', 'Mail'), ('admin', 'Admin'), ('api', 'API'),
        ('cdn', 'CDN'), ('unknown', 'Unknown'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='subdomain_findings')
    subdomain = models.CharField(max_length=500)
    source = models.CharField(max_length=50)  # crt_sh, user_submitted
    resolves_to = models.GenericIPAddressField(null=True, blank=True)
    is_alive = models.BooleanField(null=True)
    category = models.CharField(max_length=30, choices=CATEGORIES, default='unknown')
    risk_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subdomain


class InfrastructureFinding(models.Model):
    INFRA_TYPES = [
        ('cloud_provider', 'Cloud Provider'), ('cdn', 'CDN'),
        ('data_center', 'Data Center'), ('colo', 'Colocation'),
        ('isp', 'ISP'), ('vpn_gateway', 'VPN Gateway'),
        ('email_provider', 'Email Provider'), ('dns_provider', 'DNS Provider'),
        ('waf', 'WAF'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='infra_findings')
    infra_type = models.CharField(max_length=30, choices=INFRA_TYPES)
    provider_name = models.CharField(max_length=255)
    evidence = models.TextField()
    ip_ranges = models.JSONField(default=list, blank=True)
    associated_domains = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(default=0.0)
    risk_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider_name} ({self.infra_type})"


class WhoisRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='whois_records')
    domain = models.CharField(max_length=255)
    registrant_name = models.CharField(max_length=255, blank=True)
    registrant_org = models.CharField(max_length=255, blank=True)
    registrar = models.CharField(max_length=255, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    name_servers = models.JSONField(default=list, blank=True)
    raw_whois = models.TextField(blank=True)
    risk_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"WHOIS {self.domain}"


class EmailSecurityAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='email_assessments')
    domain = models.CharField(max_length=255)
    has_spf = models.BooleanField(default=False)
    spf_record = models.TextField(blank=True)
    spf_assessment = models.CharField(max_length=50, blank=True)
    has_dkim = models.BooleanField(null=True)
    has_dmarc = models.BooleanField(default=False)
    dmarc_record = models.TextField(blank=True)
    dmarc_policy = models.CharField(max_length=20, blank=True)
    mx_providers = models.JSONField(default=list, blank=True)
    overall_grade = models.CharField(max_length=5, blank=True)
    risk_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email security: {self.domain} (grade: {self.overall_grade or 'unknown'})"


class ScreenshotUpload(models.Model):
    SOURCE_CHOICES = [
        ('dnsdumpster', 'DNSDumpster'), ('shodan', 'Shodan'), ('other', 'Other'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='screenshots')
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    image = models.ImageField(upload_to='osint_screenshots/')
    caption = models.CharField(max_length=500, blank=True)
    analysis = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} screenshot for {self.osint_job.organization_name}"


class TerminalSubmission(models.Model):
    COMMAND_TYPES = [
        ('dig', 'dig'), ('whois', 'whois'), ('curl', 'curl'),
        ('nslookup', 'nslookup'), ('arin', 'ARIN Lookup'), ('other', 'Other'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='terminal_submissions')
    command_type = models.CharField(max_length=20, choices=COMMAND_TYPES)
    command_text = models.TextField()
    output_text = models.TextField()
    parsed_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.command_type} submission for {self.osint_job.organization_name}"


class OsintReportSection(models.Model):
    SECTION_TYPES = [
        ('cover', 'Cover Page'),
        ('executive_summary', 'Executive Summary'),
        ('remediation_plan', 'Remediation Action Plan'),
        ('security_roadmap', 'Strategic Security Roadmap'),
        ('entity_findings', 'Detailed Findings'),
        ('regulatory_landscape', 'Regulatory Compliance Landscape'),
        ('engagement_proposal', 'Engagement Proposal'),
        ('methodology', 'OSINT Methodology'),
        ('infrastructure_maps', 'Infrastructure Maps'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='report_sections')
    section_type = models.CharField(max_length=30, choices=SECTION_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    structured_data = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['osint_job', 'section_type']

    def __str__(self):
        return f"{self.section_type}: {self.osint_job.organization_name}"


class ServiceMapping(models.Model):
    SERVICE_CHOICES = [
        ('mdr_soc', 'MDR/SOC/Threat Monitoring'),
        ('pen_test', 'Pen Testing/Red Team/ASM'),
        ('vciso_grc', 'vCISO/GRC/Compliance Advisory'),
        ('ir_retainer', 'IR Retainer/Incident Response'),
        ('infrastructure', 'Infrastructure Services'),
        ('digital_workplace', 'Digital Workplace'),
        ('app_modernization', 'Application Modernization'),
        ('ai_ops', 'AI/Intelligent Operations'),
        ('field_cto', 'Field CTO/Strategic Advisory'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    osint_job = models.ForeignKey(OsintJob, on_delete=models.CASCADE, related_name='service_mappings')
    service = models.CharField(max_length=30, choices=SERVICE_CHOICES)
    finding_summary = models.TextField()
    urgency = models.CharField(max_length=20)  # immediate, short_term, strategic
    justification = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service} → {self.osint_job.organization_name}"
```

---

## Step 5 — Migrations

```bash
python manage.py makemigrations osint
python manage.py migrate
```

Verify migration creates all tables:
```bash
python manage.py dbshell
# \dt osint_*   (lists all osint tables)
```

---

## Step 6 — Admin Registration

**File:** `backend/osint/admin.py`

```python
from django.contrib import admin
from .models import (
    OsintJob, DnsFinding, SubdomainFinding, InfrastructureFinding,
    WhoisRecord, EmailSecurityAssessment, ScreenshotUpload,
    TerminalSubmission, OsintReportSection, ServiceMapping,
)

@admin.register(OsintJob)
class OsintJobAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'primary_domain', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['organization_name', 'primary_domain']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(DnsFinding)
class DnsFindingAdmin(admin.ModelAdmin):
    list_display = ['domain', 'record_type', 'risk_level', 'osint_job']
    list_filter = ['record_type', 'risk_level']

@admin.register(SubdomainFinding)
class SubdomainFindingAdmin(admin.ModelAdmin):
    list_display = ['subdomain', 'category', 'is_alive', 'osint_job']
    list_filter = ['category', 'source']

@admin.register(EmailSecurityAssessment)
class EmailSecurityAdmin(admin.ModelAdmin):
    list_display = ['domain', 'has_spf', 'has_dmarc', 'dmarc_policy', 'overall_grade']

admin.site.register(InfrastructureFinding)
admin.site.register(WhoisRecord)
admin.site.register(ScreenshotUpload)
admin.site.register(TerminalSubmission)
admin.site.register(OsintReportSection)
admin.site.register(ServiceMapping)
```

---

## Step 7 — Serializer Scaffolding

**File:** `backend/osint/serializers.py`

```python
from rest_framework import serializers
from .models import (
    OsintJob, DnsFinding, SubdomainFinding, InfrastructureFinding,
    WhoisRecord, EmailSecurityAssessment, ScreenshotUpload,
    TerminalSubmission, OsintReportSection, ServiceMapping,
)


class OsintJobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OsintJob
        fields = ['organization_name', 'primary_domain', 'additional_domains',
                  'engagement_context', 'research_job']


class OsintJobSerializer(serializers.ModelSerializer):
    findings_summary = serializers.SerializerMethodField()
    phase_progress = serializers.SerializerMethodField()

    class Meta:
        model = OsintJob
        fields = '__all__'
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def get_findings_summary(self, obj):
        return {
            'subdomains_found': obj.subdomain_findings.count(),
            'dns_records': obj.dns_findings.count(),
            'email_assessments': obj.email_assessments.count(),
            'screenshots': obj.screenshots.count(),
        }

    def get_phase_progress(self, obj):
        status = obj.status
        phases = {
            'phase1': 'pending',
            'phase2_auto': 'pending',
            'phase2_manual': 'pending',
            'phase3': 'pending',
            'phase4': 'pending',
            'phase5': 'pending',
        }
        status_order = [
            'phase1_research', 'phase1_complete', 'phase2_auto',
            'awaiting_terminal_output', 'phase2_processing',
            'awaiting_screenshots', 'phase3_processing',
            'phase4_analysis', 'phase5_report', 'completed',
        ]
        if status in status_order:
            idx = status_order.index(status)
            if idx >= 1: phases['phase1'] = 'completed'
            if idx >= 3: phases['phase2_auto'] = 'completed'
            if idx >= 5: phases['phase2_manual'] = 'completed'
            if idx >= 7: phases['phase3'] = 'completed'
            if idx >= 8: phases['phase4'] = 'completed'
            if idx >= 9: phases['phase5'] = 'completed'
        return phases


class DnsFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DnsFinding
        fields = '__all__'


class SubdomainFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubdomainFinding
        fields = '__all__'


class InfrastructureFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureFinding
        fields = '__all__'


class EmailSecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSecurityAssessment
        fields = '__all__'


class ScreenshotUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreenshotUpload
        fields = '__all__'
        read_only_fields = ['analysis', 'extracted_data']


class ServiceMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceMapping
        fields = '__all__'
```

---

## Step 8 — URL Scaffolding (stub views)

**File:** `backend/osint/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('jobs/', views.OsintJobListCreateView.as_view(), name='osint-list-create'),
    path('jobs/<uuid:pk>/', views.OsintJobDetailView.as_view(), name='osint-detail'),
    path('jobs/<uuid:pk>/execute/', views.OsintJobExecuteView.as_view(), name='osint-execute'),
    path('jobs/<uuid:pk>/commands/', views.OsintCommandsView.as_view(), name='osint-commands'),
    path('jobs/<uuid:pk>/submit-terminal-output/', views.SubmitTerminalOutputView.as_view(), name='osint-submit-terminal'),
    path('jobs/<uuid:pk>/submit-screenshots/', views.SubmitScreenshotsView.as_view(), name='osint-submit-screenshots'),
    path('jobs/<uuid:pk>/skip-screenshots/', views.SkipScreenshotsView.as_view(), name='osint-skip-screenshots'),
    path('jobs/<uuid:pk>/generate-report/', views.GenerateReportView.as_view(), name='osint-generate-report'),
    path('jobs/<uuid:pk>/report/', views.DownloadReportView.as_view(), name='osint-download-report'),
    path('jobs/<uuid:pk>/subdomains/', views.SubdomainListView.as_view(), name='osint-subdomains'),
    path('jobs/<uuid:pk>/dns/', views.DnsFindingListView.as_view(), name='osint-dns'),
    path('jobs/<uuid:pk>/email-security/', views.EmailSecurityListView.as_view(), name='osint-email-security'),
    path('jobs/<uuid:pk>/infrastructure/', views.InfrastructureListView.as_view(), name='osint-infrastructure'),
    path('jobs/<uuid:pk>/service-mappings/', views.ServiceMappingListView.as_view(), name='osint-service-mappings'),
]
```

**File:** `backend/osint/views.py` (stub — all views raise `NotImplementedError` for now, filled in Plans 03–07):

```python
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status as http_status
from .models import OsintJob, DnsFinding, SubdomainFinding, EmailSecurityAssessment, InfrastructureFinding, ServiceMapping
from .serializers import (
    OsintJobCreateSerializer, OsintJobSerializer,
    DnsFindingSerializer, SubdomainFindingSerializer,
    EmailSecuritySerializer, InfrastructureFindingSerializer,
    ServiceMappingSerializer,
)


class OsintJobListCreateView(ListCreateAPIView):
    queryset = OsintJob.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OsintJobCreateSerializer
        return OsintJobSerializer


class OsintJobDetailView(RetrieveAPIView):
    queryset = OsintJob.objects.all()
    serializer_class = OsintJobSerializer


class OsintJobExecuteView(APIView):
    def post(self, request, pk):
        return Response({'detail': 'Not implemented yet'}, status=http_status.HTTP_501_NOT_IMPLEMENTED)


class OsintCommandsView(APIView):
    def get(self, request, pk):
        return Response({'detail': 'Not implemented yet'}, status=http_status.HTTP_501_NOT_IMPLEMENTED)


class SubmitTerminalOutputView(APIView):
    def post(self, request, pk):
        return Response({'detail': 'Not implemented yet'}, status=http_status.HTTP_501_NOT_IMPLEMENTED)


class SubmitScreenshotsView(APIView):
    def post(self, request, pk):
        return Response({'detail': 'Not implemented yet'}, status=http_status.HTTP_501_NOT_IMPLEMENTED)


class SkipScreenshotsView(APIView):
    def post(self, request, pk):
        return Response({'detail': 'Not implemented yet'}, status=http_status.HTTP_501_NOT_IMPLEMENTED)


class GenerateReportView(APIView):
    def post(self, request, pk):
        return Response({'detail': 'Not implemented yet'}, status=http_status.HTTP_501_NOT_IMPLEMENTED)


class DownloadReportView(APIView):
    def get(self, request, pk):
        return Response({'detail': 'Not implemented yet'}, status=http_status.HTTP_501_NOT_IMPLEMENTED)


class SubdomainListView(APIView):
    def get(self, request, pk):
        job = OsintJob.objects.get(pk=pk)
        serializer = SubdomainFindingSerializer(job.subdomain_findings.all(), many=True)
        return Response(serializer.data)


class DnsFindingListView(APIView):
    def get(self, request, pk):
        job = OsintJob.objects.get(pk=pk)
        serializer = DnsFindingSerializer(job.dns_findings.all(), many=True)
        return Response(serializer.data)


class EmailSecurityListView(APIView):
    def get(self, request, pk):
        job = OsintJob.objects.get(pk=pk)
        serializer = EmailSecuritySerializer(job.email_assessments.all(), many=True)
        return Response(serializer.data)


class InfrastructureListView(APIView):
    def get(self, request, pk):
        job = OsintJob.objects.get(pk=pk)
        serializer = InfrastructureFindingSerializer(job.infra_findings.all(), many=True)
        return Response(serializer.data)


class ServiceMappingListView(APIView):
    def get(self, request, pk):
        job = OsintJob.objects.get(pk=pk)
        serializer = ServiceMappingSerializer(job.service_mappings.all(), many=True)
        return Response(serializer.data)
```

---

## Step 9 — Install New Dependencies

```bash
cd backend
source venv/bin/activate
pip install dnspython python-whois python-docx httpx Pillow
pip freeze > requirements.txt
```

---

## Verification

```bash
cd backend
source venv/bin/activate
python manage.py migrate  # should apply cleanly
pytest osint/tests/test_models.py -v  # all model tests pass
python manage.py check  # no errors
curl -X POST http://localhost:8000/api/osint/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Test Corp", "primary_domain": "testcorp.com"}'
# Should return 201 with a UUID id and status: "pending"
```

---

## Done When

- [ ] `pytest osint/tests/test_models.py` passes (100%)
- [ ] `python manage.py migrate` applies cleanly with no errors
- [ ] `POST /api/osint/jobs/` returns 201 with correct fields
- [ ] `GET /api/osint/jobs/{id}/` returns job with `findings_summary` and `phase_progress`
- [ ] `python manage.py check` passes
