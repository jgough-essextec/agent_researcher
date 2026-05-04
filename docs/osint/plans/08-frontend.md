# Plan 08 — Frontend: Pages, Components, Types & API Client

**Depends on:** Plans 01–07 (all backend complete)  
**This is the final plan.**

---

## Goal

Build the complete frontend for the OSINT feature: 3 new pages, 30+ components, TypeScript types, and API client additions. The design philosophy: **the phase stepper communicates sequential human-gated workflow; results tabs are lazy-loaded once Phase 4 completes**.

---

## Files to Create / Modify

### New Files

```
frontend/
  app/
    osint/
      page.tsx                    (OSINT job list)
      new/
        page.tsx                  (creation form)
    [id]/
        page.tsx                  (phase workflow + results)

  components/
    osint/
      OsintLaunchPanel.tsx        (9th tab entry point from research results)
      PhasesStepper.tsx           (left rail phase progress)
      phase-panels/
        Phase1RunningPanel.tsx
        Phase2DnsPanel.tsx        (the complex human-in-the-loop UI)
        Phase3ScreenshotPanel.tsx
        Phase4AnalysisPanel.tsx
        Phase5ReportPanel.tsx
        shared/
          CommandBlock.tsx        (syntax-highlighted commands + Copy All)
          OutputTextarea.tsx      (paste target with line count)
          AnalyzingPanel.tsx      (progress while AI analyzes)
          PreviousRoundAccordion.tsx
          CannotRunModal.tsx
          SiteInstructionCard.tsx (for DNSDumpster/Shodan steps)
          ScreenshotUploader.tsx  (drag-drop with source labeling)
      results-tabs/
        OverviewTab.tsx
        InfrastructureTab.tsx
        EmailSecurityTab.tsx
        TechStackTab.tsx
        FindingsTab.tsx
        RemediationTab.tsx
        ReportTab.tsx
      shared/
        SeverityBadge.tsx
        RiskHeatMap.tsx
        SubdomainTable.tsx
        EmailSecurityPanel.tsx
        TechStackGrid.tsx
        RemediationTimeline.tsx
        ServicesMappingPanel.tsx
        ServiceDetailDrawer.tsx

  types/
    osint.ts                      (all OSINT TypeScript interfaces)
```

### Modified Files

- `frontend/lib/api.ts` — add OSINT API methods
- `frontend/components/research-results/index.tsx` — add 9th tab
- `frontend/app/projects/[id]/page.tsx` — add OSINT entry button

---

## Step 1 — TypeScript Types

**File:** `frontend/types/osint.ts`

```typescript
// Phase lifecycle
export type OsintPhaseStatus =
  | 'locked' | 'active' | 'waiting_for_input' | 'processing' | 'done' | 'failed';

export type OsintPhaseNumber = 1 | 2 | 3 | 4 | 5;

export type PelleraService =
  | 'mdr_soc' | 'pen_test' | 'vciso_grc' | 'ir_retainer'
  | 'infrastructure' | 'digital_workplace' | 'app_modernization'
  | 'ai_ops' | 'field_cto';

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type Likelihood = 1 | 2 | 3 | 4 | 5;
export type ImpactLevel = 1 | 2 | 3 | 4 | 5;

export type DnsRecordType = 'A' | 'AAAA' | 'MX' | 'TXT' | 'NS' | 'CNAME' | 'SOA' | 'DMARC' | 'SPF';
export type SubdomainCategory = 'production' | 'staging' | 'dev' | 'vpn' | 'mail' | 'admin' | 'api' | 'cdn' | 'unknown';
export type SpfStatus = 'present' | 'fail_all' | 'missing';
export type DmarcPolicy = 'reject' | 'quarantine' | 'none' | 'missing' | 'unknown';
export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type RemediationPhase = '0-30' | '30-90' | '90-180';

export interface OsintJob {
  id: string;
  organization_name: string;
  primary_domain: string;
  additional_domains: string[];
  engagement_context: string;
  research_job: string | null;
  status: string;
  current_step: string;
  error: string;
  phase_progress: {
    phase1: OsintPhaseStatus;
    phase2_auto: OsintPhaseStatus;
    phase2_manual: OsintPhaseStatus;
    phase3: OsintPhaseStatus;
    phase4: OsintPhaseStatus;
    phase5: OsintPhaseStatus;
  };
  findings_summary: {
    subdomains_found: number;
    dns_records: number;
    email_assessments: number;
    screenshots: number;
  };
  report_file: string | null;
  created_at: string;
  updated_at: string;
}

export interface OsintCommandRound {
  round_number: number;
  commands: string[];
  rationale: string;
  output_submitted: boolean;
}

export interface OsintCommandsResponse {
  job_id: string;
  organization_name: string;
  primary_domain: string;
  rounds: OsintCommandRound[];
}

export interface DnsFinding {
  id: string;
  domain: string;
  record_type: DnsRecordType;
  record_value: string;
  analysis: string;
  risk_level: Severity | '';
}

export interface SubdomainFinding {
  id: string;
  subdomain: string;
  source: string;
  resolves_to: string | null;
  is_alive: boolean | null;
  category: SubdomainCategory;
  risk_notes: string;
}

export interface EmailSecurityFinding {
  id: string;
  domain: string;
  has_spf: boolean;
  spf_record: string;
  spf_assessment: SpfStatus;
  has_dmarc: boolean;
  dmarc_record: string;
  dmarc_policy: DmarcPolicy;
  mx_providers: string[];
  overall_grade: string;
  risk_summary: string;
}

export interface TechStackEntry {
  id: string;
  vendor: string;
  product: string | null;
  category: string;
  evidence_source: string[];
  confidence: ConfidenceLevel;
  pellera_service_relevance: PelleraService[];
}

export interface InfrastructureFinding {
  id: string;
  infra_type: string;
  provider_name: string;
  evidence: string;
  ip_ranges: string[];
  confidence: number;
  risk_notes: string;
}

export interface ServiceMapping {
  id: string;
  service: PelleraService;
  finding_summary: string;
  urgency: 'immediate' | 'short_term' | 'strategic';
  justification: string;
}

export interface CreateOsintJobParams {
  organization_name: string;
  primary_domain: string;
  additional_domains?: string[];
  engagement_context?: string;
  research_job?: string | null;
}

export interface TerminalSubmission {
  command_type: string;
  command_text: string;
  output_text: string;
}
```

---

## Step 2 — API Client Additions

**Add to `frontend/lib/api.ts`:**

```typescript
// --- OSINT ---

export const createOsintJob = async (params: CreateOsintJobParams): Promise<OsintJob> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const getOsintJob = async (id: string): Promise<OsintJob> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const listOsintJobs = async (): Promise<OsintJob[]> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const executeOsintJob = async (id: string): Promise<OsintJob> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/execute/`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const getOsintCommands = async (id: string): Promise<OsintCommandsResponse> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/commands/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const submitTerminalOutput = async (
  id: string,
  submissions: TerminalSubmission[]
): Promise<OsintJob> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/submit-terminal-output/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ submissions }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const uploadScreenshot = async (
  id: string,
  file: File,
  source: string,
  caption?: string
): Promise<{ screenshot_id: string }> => {
  const form = new FormData();
  form.append('image', file);
  form.append('source', source);
  if (caption) form.append('caption', caption);
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/submit-screenshots/`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const skipScreenshots = async (id: string): Promise<void> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/skip-screenshots/`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
};

export const generateReport = async (id: string): Promise<void> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/generate-report/`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
};

export const getOsintReportDownloadUrl = (id: string): string =>
  `${API_BASE}/api/osint/jobs/${id}/report/`;

// Lazy-loaded findings endpoints
export const getSubdomainFindings = async (id: string): Promise<SubdomainFinding[]> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/subdomains/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const getEmailSecurityFindings = async (id: string): Promise<EmailSecurityFinding[]> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/email-security/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const getInfrastructureFindings = async (id: string): Promise<InfrastructureFinding[]> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/infrastructure/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const getServiceMappings = async (id: string): Promise<ServiceMapping[]> => {
  const res = await fetch(`${API_BASE}/api/osint/jobs/${id}/service-mappings/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};
```

---

## Step 3 — Key Component Specifications

### `PhasesStepper.tsx`

```typescript
// Props
interface PhasesStepperProps {
  phaseProgress: OsintJob['phase_progress'];
  currentStatus: string;
  onPhaseClick: (phase: OsintPhaseNumber) => void;
}

// Phase labels and the status fields they map to
const PHASES: { num: OsintPhaseNumber; label: string; key: keyof OsintJob['phase_progress'] }[] = [
  { num: 1, label: 'Web Research', key: 'phase1' },
  { num: 2, label: 'DNS & Infrastructure', key: 'phase2_auto' },
  { num: 3, label: 'Browser OSINT', key: 'phase3' },
  { num: 4, label: 'Analysis', key: 'phase4' },
  { num: 5, label: 'Final Report', key: 'phase5' },
];
```

Styling rules:
- `done` → green check icon + green text, clickable to scroll to phase summary
- `active` / `waiting_for_input` / `processing` → blue pulsing dot
- `locked` → grey lock icon, not clickable
- On mobile (`md:hidden`): render as horizontal progress bar with phase number badges only

### `CommandBlock.tsx`

```typescript
interface CommandBlockProps {
  commands: string[];
  round: number;
  totalRounds: number;
}
```

- Dark background: `bg-gray-900 rounded-lg p-4`
- Each command: `<div className="font-mono text-sm"><span className="text-gray-500 select-none">$ </span><span className="text-green-300">{cmd}</span></div>`
- "Copy All" button: copies `commands.join('\n')` to clipboard. `useState` for 2-second "Copied!" state
- Hover-reveal per-line copy icon using `group` and `opacity-0 group-hover:opacity-100`

### `OutputTextarea.tsx`

```typescript
interface OutputTextareaProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}
```

- `className="font-mono text-sm min-h-[200px] max-h-[500px] resize-none w-full"`
- Show "X lines pasted" count below textarea when value is non-empty: `value.split('\n').filter(Boolean).length`

### `RiskHeatMap.tsx`

```typescript
interface RiskItem {
  finding: string;
  likelihood: Likelihood;
  impact: ImpactLevel;
  severity: Severity;
}

interface RiskHeatMapProps {
  items: RiskItem[];
}
```

Pure CSS 5×5 grid implementation:
```typescript
const getRiskCellColor = (row: number, col: number): string => {
  const score = row * col; // row = likelihood (1-5), col = impact (1-5)
  if (score >= 15) return 'bg-red-600';
  if (score >= 9) return 'bg-orange-500';
  if (score >= 4) return 'bg-yellow-400';
  return 'bg-green-400';
};

// Grid: 5 rows (likelihood 5 at top → 1 at bottom) × 5 cols (impact 1 left → 5 right)
// Finding dots: absolutely positioned within their cell, Radix Tooltip on hover
```

### `SeverityBadge.tsx`

```typescript
const SEVERITY_STYLES: Record<Severity, string> = {
  critical: 'bg-red-100 text-red-800 border border-red-300',
  high: 'bg-orange-100 text-orange-800 border border-orange-300',
  medium: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
  low: 'bg-green-100 text-green-800 border border-green-300',
  info: 'bg-blue-100 text-blue-800 border border-blue-300',
};
```

### `EmailSecurityPanel.tsx`

Three status cards rendered side-by-side (or stacked on mobile). Each shows:
- Label (SPF / DKIM / DMARC)
- Status indicator (PASS ✓ / MISSING ✗ / policy=quarantine)
- Color background: green for good, orange for partial, red for missing/fail
- Raw record value in a collapsible `<details>` / accordion below cards

### `ScreenshotUploader.tsx`

- Drop zone: HTML5 `onDragOver`/`onDrop`, no library
- `<input type="file" accept="image/png,image/jpeg,image/webp" multiple />` hidden, triggered by click
- Preview row per file: `<img>` thumbnail (60×45px object-cover), filename, source dropdown, remove button
- Source dropdown options: "DNSDumpster", "Shodan", "Other"
- Upload happens on form submit, not on drop

---

## Step 4 — Page Implementations

### `/osint/new/page.tsx`

Two-section form:
1. **Core Identity** (required): Prospect Name, Primary Domain, Industry, Approx Size, HQ Location
2. **Known Context** (optional, collapsible): Description, Subsidiaries (TagInput), Known Technologies (TagInput), linked Research Job (hidden/read-only if from query param)

On submit: `createOsintJob(params)` → redirect to `/osint/{id}`.

Pre-populate from query params: `?researchJobId=X&name=Y&domain=Z&industry=W`

Show `ResearchContextBanner` if `researchJobId` is present.

### `/osint/[id]/page.tsx`

Layout:
```
┌─────────────────────────────────────────────────────────┐
│  Organization Name                 [Pellera Technologies]│
│  acme.com                                               │
├──────────────┬──────────────────────────────────────────┤
│ PhasesStepper│  <Phase Panel — changes with status>     │
│ (sticky,     │                                          │
│  left rail)  │  [Results Tabs — appear after Phase 4]  │
└──────────────┴──────────────────────────────────────────┘
```

Polling: `useEffect` with `setInterval(3000)` while `status` not in `['completed', 'failed']`. Clear interval on unmount.

Phase panel routing by `job.status`:
- `phase1_research` → `<Phase1RunningPanel />`
- `awaiting_terminal_output` → `<Phase2DnsPanel />`
- `phase2_processing` → `<AnalyzingPanel message="Analysing DNS output..." />`
- `awaiting_screenshots` → `<Phase3ScreenshotPanel />`
- `phase3_processing` → `<AnalyzingPanel message="Analysing screenshots..." />`
- `phase4_analysis` → `<Phase4AnalysisPanel />`
- `phase5_report` / `completed` → `<Phase5ReportPanel />`

Results tabs appear (slide in) when `phase_progress.phase4 === 'done'`.

### `/osint/page.tsx`

List page mirroring `/projects`. Table with columns: Prospect, Domain, Status badge, Created, Actions (View, Download if completed).

---

## Step 5 — Research Results Integration (9th Tab)

**Modify `frontend/components/research-results/index.tsx`:**

Add `{ id: 'osint', label: 'OSINT Deep Dive' }` to the tabs array. The tab renders `<OsintLaunchPanel researchJob={job} />`.

**`OsintLaunchPanel.tsx`:**

```typescript
interface OsintLaunchPanelProps {
  researchJob: ResearchJob;
}
```

Shows:
- Heading: "OSINT Infrastructure Assessment"
- Brief description of what OSINT will do
- If no linked OSINT job: a "Launch OSINT Analysis" button → navigates to `/osint/new?researchJobId={id}&name={company}&domain={domain}`
- If linked OSINT job exists (query `listOsintJobs()` filtered by `research_job === researchJob.id`): shows job status + link to `/osint/{id}`

**Modify `frontend/app/projects/[id]/page.tsx`:**

Add "Add OSINT Analysis" button next to existing "Run New Iteration" button. Links to `/osint/new?projectId={projectId}&researchJobId={latestIterationId}`.

---

## Step 6 — Results Tabs Implementation Notes

All results tabs lazy-load their data on first render using a local `useEffect` + `useState` pattern (not context) — mirrors the existing tab pattern in the app.

**OverviewTab:** Most important tab. Show `RiskHeatMap` prominently at top, then top 5 severity findings list, then summary stats (subdomain count, email grade, tech vendor count).

**InfrastructureTab:** `SubdomainTable` (filterable by category, sortable by risk). Separate section for IP/ASN mapping from infrastructure findings.

**EmailSecurityTab:** `EmailSecurityPanel` with 3 status cards + raw records. One panel per domain assessed (primary + any subsidiaries).

**TechStackTab:** `TechStackGrid` — card per vendor. Filter by Pellera service relevance.

**FindingsTab:** Filterable table. Left border severity strip (4px). Filter by: severity, category. Default sort: severity desc.

**RemediationTab:** `RemediationTimeline` (3 columns: 0-30, 30-90, 90-180 days). `ServicesMappingPanel` below it. `ServiceDetailDrawer` slide-out on "Learn →" click.

**ReportTab:** In-app ToC preview. "Generate Full Report" button. Polling for `status === 'completed'`. Download via `<a href={getOsintReportDownloadUrl(id)} download>`.

---

## Mobile Responsiveness

- Phase stepper: horizontal progress bar on `< md`
- Phase 2 terminal commands: add notice "This step works best on desktop. You can still copy commands and paste output here from a mobile terminal app."
- Results tabs: horizontal scroll wrapper on mobile (`overflow-x-auto`)
- RiskHeatMap: `w-8 h-8` cells on mobile vs `w-12 h-12` on desktop
- SubdomainTable: horizontal scroll on mobile

---

## Verification

```bash
cd frontend
npm run build            # no TypeScript errors
npm run lint             # no ESLint warnings
npm run test             # unit tests pass

# Manual browser testing:
# 1. Navigate to / → create a research job and wait for completion
# 2. Open research results → click "OSINT Deep Dive" tab → click "Launch OSINT Analysis"
# 3. Confirm form pre-fills with research job data
# 4. Submit form → confirm redirect to /osint/{id}
# 5. Confirm Phase 1 panel shows running state
# 6. Wait for awaiting_terminal_output → confirm Phase 2 panel with commands
# 7. Copy commands, run in terminal, paste output
# 8. Confirm transition to awaiting_screenshots
# 9. Upload a real screenshot from dnsdumpster.com
# 10. Wait for phase4_analysis → confirm results tabs appear
# 11. Click through all 7 tabs, verify data renders
# 12. Click "Generate Report" in Report tab
# 13. Wait for completed → download .docx, verify it opens correctly
```

---

## Done When

- [ ] `npm run build` completes with no TypeScript errors
- [ ] `npm run lint` passes
- [ ] `/osint/new` creation form works, validates domain format, submits
- [ ] `/osint/[id]` phase stepper reflects backend status correctly
- [ ] Phase 2 `CommandBlock` "Copy All" button works
- [ ] Phase 2 textarea accepts pasted output, submits, and transitions status
- [ ] Phase 3 screenshot uploader accepts files, labels by source, uploads
- [ ] All 7 results tabs load their data lazily
- [ ] `RiskHeatMap` renders without D3 (pure CSS grid + Tailwind)
- [ ] 9th "OSINT Deep Dive" tab appears on research results page
- [ ] Report tab "Generate Report" → download `.docx` works end-to-end
- [ ] No regressions in existing research/project functionality
