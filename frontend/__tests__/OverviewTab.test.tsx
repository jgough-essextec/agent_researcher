import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import OverviewTab from '@/components/research-results/tabs/OverviewTab';
import { ResearchJob, ResearchReport, WebSource } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const sources: WebSource[] = [
  { uri: 'https://source1.com', title: 'Source One' },
];

const fullReport: ResearchReport = {
  id: 'r1',
  company_overview: 'A global technology company specialising in cloud services.',
  founded_year: 2001,
  headquarters: 'Seattle, WA',
  employee_count: '12,000',
  annual_revenue: '$4.5B',
  website: 'https://example.com',
  recent_news: [],
  decision_makers: [
    { name: 'Jane Doe', title: 'CIO', background: 'Former Google exec.' },
  ],
  pain_points: ['ERP fragmentation', 'Manual reporting'],
  opportunities: ['Cloud migration', 'AI adoption [1]'],
  digital_maturity: 'maturing',
  ai_footprint: 'Piloting **Copilot** for productivity.',
  ai_adoption_stage: 'implementing',
  strategic_goals: ['Become cloud-first by 2026'],
  key_initiatives: ['Project Phoenix (ERP consolidation)'],
  talking_points: ['How are you handling multi-cloud governance?'],
  data_maturity: 'Uses **Snowflake** and Power BI for analytics.',
  web_sources: sources,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const minimalJob: ResearchJob = {
  id: 'j1',
  client_name: 'TestCo',
  sales_history: '',
  prompt: '',
  status: 'completed',
  result: '',
  error: '',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const fullJob: ResearchJob = { ...minimalJob, report: fullReport };

describe('OverviewTab', () => {
  // --- 1. Null report shows fallback ---
  it('shows fallback when report is null', () => {
    render(<OverviewTab job={minimalJob} />);
    expect(screen.getByText('Structured data not available for this research job.')).toBeTruthy();
  });

  // --- 2. Null report does not crash ---
  it('does not crash when report is absent', () => {
    const { container } = render(<OverviewTab job={minimalJob} />);
    expect(container).toBeTruthy();
  });

  // --- 3. Company overview ---
  it('renders company_overview text', () => {
    render(<OverviewTab job={fullJob} sources={sources} />);
    expect(screen.getByText('A global technology company specialising in cloud services.')).toBeTruthy();
    expect(screen.getByText('Company Overview')).toBeTruthy();
  });

  // --- 4. Stat cards ---
  it('renders stat cards for founded_year, employee_count, annual_revenue, digital_maturity', () => {
    render(<OverviewTab job={fullJob} sources={sources} />);
    expect(screen.getByText('2001')).toBeTruthy();
    expect(screen.getByText('12,000')).toBeTruthy();
    expect(screen.getByText('$4.5B')).toBeTruthy();
    expect(screen.getByText('maturing')).toBeTruthy();
  });

  // --- 5. Decision makers ---
  it('renders decision maker name and title', () => {
    render(<OverviewTab job={fullJob} sources={sources} />);
    expect(screen.getByText('Jane Doe')).toBeTruthy();
    expect(screen.getByText('CIO')).toBeTruthy();
    expect(screen.getByText('Former Google exec.')).toBeTruthy();
    expect(screen.getByText('Key Decision Makers')).toBeTruthy();
  });

  // --- 6. Pain points ---
  it('renders pain points list', () => {
    render(<OverviewTab job={fullJob} sources={sources} />);
    expect(screen.getByText('Pain Points')).toBeTruthy();
    expect(screen.getByText('ERP fragmentation')).toBeTruthy();
    expect(screen.getByText('Manual reporting')).toBeTruthy();
  });

  // --- 7. Opportunities ---
  it('renders opportunities list', () => {
    render(<OverviewTab job={fullJob} sources={sources} />);
    expect(screen.getByText('Opportunities')).toBeTruthy();
    expect(screen.getByText('Cloud migration')).toBeTruthy();
  });

  // --- 8. Talking points ---
  it('renders talking points', () => {
    render(<OverviewTab job={fullJob} sources={sources} />);
    expect(screen.getByText('Recommended Talking Points')).toBeTruthy();
    expect(screen.getByText('How are you handling multi-cloud governance?')).toBeTruthy();
  });

  // --- 9. Data maturity prose (not a stat card) ---
  it('renders data_maturity as prose via MarkdownText, not a truncated stat card', () => {
    render(<OverviewTab job={fullJob} sources={sources} />);
    expect(screen.getByText('Data Maturity')).toBeTruthy();
    // Markdown ** should render as <strong>, not raw **
    expect(screen.queryByText(/\*\*Snowflake\*\*/)).toBeNull();
    const strongs = document.querySelectorAll('strong');
    const strongTexts = Array.from(strongs).map(s => s.textContent);
    expect(strongTexts.some(t => t?.includes('Snowflake'))).toBe(true);
  });

  // --- 10. Empty optional arrays don't render sections ---
  it('hides decision makers section when empty', () => {
    const report = { ...fullReport, decision_makers: [] };
    const job = { ...fullJob, report };
    render(<OverviewTab job={job} />);
    expect(screen.queryByText('Key Decision Makers')).toBeNull();
  });

  it('hides pain points section when empty', () => {
    const report = { ...fullReport, pain_points: [] };
    const job = { ...fullJob, report };
    render(<OverviewTab job={job} />);
    expect(screen.queryByText('Pain Points')).toBeNull();
  });

  it('hides talking points section when empty', () => {
    const report = { ...fullReport, talking_points: [] };
    const job = { ...fullJob, report };
    render(<OverviewTab job={job} />);
    expect(screen.queryByText('Recommended Talking Points')).toBeNull();
  });

  // --- 11. Citation badges rendered via MarkdownText (data_maturity) ---
  it('renders citation badge for [1] in data_maturity when sources provided', () => {
    const report = { ...fullReport, data_maturity: 'Uses **Snowflake** for analytics [1].' };
    const job = { ...fullJob, report };
    render(<OverviewTab job={job} sources={sources} />);
    const sups = document.querySelectorAll('sup');
    const supTexts = Array.from(sups).map(s => s.textContent?.trim());
    expect(supTexts.some(t => t === '1')).toBe(true);
  });
});
