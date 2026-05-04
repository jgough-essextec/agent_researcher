export type OsintPhaseStatus =
  | 'locked' | 'active' | 'waiting_for_input' | 'processing' | 'done' | 'failed';

export type PelleraService =
  | 'mdr_soc' | 'pen_test' | 'vciso_grc' | 'ir_retainer'
  | 'infrastructure' | 'digital_workplace' | 'app_modernization'
  | 'ai_ops' | 'field_cto';

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type DmarcPolicy = 'reject' | 'quarantine' | 'none' | 'missing' | 'unknown';
export type ConfidenceLevel = 'high' | 'medium' | 'low';

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
    phase1: string;
    phase2_auto: string;
    phase2_manual: string;
    phase3: string;
    phase4: string;
    phase5: string;
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

export interface SubdomainFinding {
  id: string;
  subdomain: string;
  source: string;
  resolves_to: string | null;
  is_alive: boolean | null;
  category: string;
  risk_notes: string;
}

export interface EmailSecurityFinding {
  id: string;
  domain: string;
  has_spf: boolean;
  spf_record: string;
  spf_assessment: string;
  has_dmarc: boolean;
  dmarc_record: string;
  dmarc_policy: DmarcPolicy;
  mx_providers: string[];
  overall_grade: string;
  risk_summary: string;
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
