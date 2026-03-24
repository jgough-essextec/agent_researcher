import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ReportTab from '@/components/research-results/tabs/ReportTab';
import { ResearchReport, WebSource } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const sources: WebSource[] = [
  { uri: 'https://source1.com', title: 'Source One' },
];

const fullReport: ResearchReport = {
  id: 'r1',
  company_overview: 'A global distribution company.',
  founded_year: 1969,
  headquarters: 'Paris, France',
  employee_count: '45,000',
  annual_revenue: '€33B',
  website: 'https://sonepar.com',
  recent_news: [
    {
      title: 'New Distribution Centre Opens',
      summary: 'Sonepar opened a new DC in Atlanta [1].',
      date: '2026-03-24',
      source: 'PR Newswire',
      url: 'https://example.com/news',
    },
  ],
  decision_makers: [],
  pain_points: ['ERP fragmentation across 40 countries'],
  opportunities: ['Azure cloud migration support [1]'],
  digital_maturity: 'maturing',
  ai_footprint: 'Piloting **agentic AI** tools for sales reps.',
  ai_adoption_stage: 'implementing',
  strategic_goals: ['Become fully digitalized omnichannel distributor'],
  key_initiatives: ['Spark omnichannel platform (2023–2028)'],
  talking_points: ['How are you handling governance across 90 brands?'],
  cloud_footprint: 'Azure Landing Zone deployed globally [1].',
  security_posture: 'SOC 2 Type II. CISO role filled in 2024.',
  data_maturity: 'Microsoft Fabric + Power BI for analytics.',
  financial_signals: ['€33.6B revenue in 2025 [1]'],
  tech_partnerships: ['Microsoft — Strategic Partner — competitive threat: no'],
  web_sources: sources,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const minimalReport: ResearchReport = {
  id: 'r2',
  company_overview: 'A small startup.',
  headquarters: '',
  employee_count: '',
  annual_revenue: '',
  website: '',
  recent_news: [],
  decision_makers: [],
  pain_points: [],
  opportunities: [],
  digital_maturity: '',
  ai_footprint: '',
  ai_adoption_stage: '',
  strategic_goals: [],
  key_initiatives: [],
  talking_points: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('ReportTab', () => {
  // --- 1. tech_partnerships as flat strings ---
  it('renders tech_partnerships as string badges without crashing', () => {
    render(<ReportTab report={fullReport} sources={sources} />);
    expect(screen.getByText('Microsoft — Strategic Partner — competitive threat: no')).toBeTruthy();
  });

  // --- 2. tech_partnerships as objects (the Sonepar crash scenario) ---
  it('renders tech_partnerships as objects without crashing — flattens to vendor — relationship_type', () => {
    const report = {
      ...fullReport,
      tech_partnerships: [
        { vendor: 'Microsoft', relationship_type: 'Azure Strategic Partner', competitive_threat: 'No' },
        { vendor: 'Publicis Sapient', relationship_type: 'Co-development partner', competitive_threat: 'No' },
      ] as unknown as string[],
    };
    render(<ReportTab report={report} sources={sources} />);
    expect(screen.getByText('Microsoft — Azure Strategic Partner')).toBeTruthy();
    expect(screen.getByText('Publicis Sapient — Co-development partner')).toBeTruthy();
  });

  // --- 3. tech_partnerships empty/absent ---
  it('hides Strategic Intelligence section when tech_partnerships is empty', () => {
    const report = { ...fullReport, tech_partnerships: [], financial_signals: [] };
    render(<ReportTab report={report} sources={sources} />);
    expect(screen.queryByText('Technology Partnerships')).toBeNull();
  });

  // --- 4. strategic_goals renders as numbered list ---
  it('renders strategic_goals as a numbered list', () => {
    render(<ReportTab report={fullReport} sources={sources} />);
    expect(screen.getByText('Become fully digitalized omnichannel distributor')).toBeTruthy();
    expect(screen.getByText('Strategic Goals')).toBeTruthy();
  });

  // --- 5. key_initiatives renders in grey boxes ---
  it('renders key_initiatives items', () => {
    render(<ReportTab report={fullReport} sources={sources} />);
    expect(screen.getByText('Spark omnichannel platform (2023–2028)')).toBeTruthy();
    expect(screen.getByText('Key Initiatives')).toBeTruthy();
  });

  // --- 6. financial_signals renders as numbered list ---
  it('renders financial_signals as a numbered list', () => {
    render(<ReportTab report={fullReport} sources={sources} />);
    expect(screen.getByText(/€33\.6B revenue in 2025/)).toBeTruthy();
    expect(screen.getByText('Financial Signals')).toBeTruthy();
  });

  // --- 7. recent_news renders with title, summary, date, source ---
  it('renders recent_news items with title and summary', () => {
    render(<ReportTab report={fullReport} sources={sources} />);
    expect(screen.getByText('New Distribution Centre Opens')).toBeTruthy();
    expect(screen.getByText(/Sonepar opened a new DC/)).toBeTruthy();
    expect(screen.getByText('2026-03-24')).toBeTruthy();
    expect(screen.getByText(/PR Newswire/)).toBeTruthy();
  });

  // --- 8. MarkdownText fields render without crash ---
  it('renders cloud_footprint, security_posture, data_maturity via MarkdownText without crashing', () => {
    render(<ReportTab report={fullReport} sources={sources} />);
    expect(screen.getByText('Cloud Footprint')).toBeTruthy();
    expect(screen.getByText('Security Posture')).toBeTruthy();
    expect(screen.getByText('Data Maturity')).toBeTruthy();
    // Verify markdown bold renders as strong, not raw **
    expect(screen.queryByText(/\*\*agentic AI\*\*/)).toBeNull();
    const boldElements = document.querySelectorAll('strong');
    expect(boldElements.length).toBeGreaterThan(0);
  });

  // --- 9. All optional fields absent — no crash ---
  it('renders without crashing when all optional fields are absent', () => {
    const { container } = render(<ReportTab report={minimalReport} />);
    expect(container).toBeTruthy();
    expect(screen.queryByText('Recent News')).toBeNull();
    expect(screen.queryByText('Strategic Goals')).toBeNull();
    expect(screen.queryByText('Key Initiatives')).toBeNull();
    expect(screen.queryByText('Strategic Intelligence')).toBeNull();
  });

  // --- 10. Minimal report (only required fields) — no crash ---
  it('renders a minimal report with only company_overview set without crashing', () => {
    const { container } = render(<ReportTab report={minimalReport} />);
    expect(container.firstChild).toBeTruthy();
  });
});
