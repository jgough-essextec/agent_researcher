import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import CompetitorsTab from '@/components/research-results/tabs/CompetitorsTab';
import { CompetitorCaseStudy } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const caseStudy: CompetitorCaseStudy = {
  id: 'cs1',
  competitor_name: 'RivalCo',
  vertical: 'retail',
  case_study_title: 'AI-Powered Demand Forecasting',
  summary: 'RivalCo deployed ML to reduce overstock by 25%.',
  technologies_used: ['Python', 'TensorFlow', 'Snowflake'],
  outcomes: ['25% overstock reduction', '$3M cost savings annually'],
  source_url: 'https://rivalco.example.com/case-study',
  relevance_score: 0.9,
  created_at: '2026-01-01T00:00:00Z',
};

const caseStudy2: CompetitorCaseStudy = {
  id: 'cs2',
  competitor_name: 'CompetitorB',
  vertical: 'technology',
  case_study_title: 'Cloud Migration at Scale',
  summary: 'Migrated 500 workloads to Azure in 12 months.',
  technologies_used: ['Azure', 'Terraform'],
  outcomes: ['40% infra cost reduction'],
  source_url: 'https://competitorb.example.com',
  relevance_score: 0.75,
  created_at: '2026-01-01T00:00:00Z',
};

describe('CompetitorsTab', () => {
  // --- 1. Count message ---
  it('renders the correct case study count message', () => {
    render(<CompetitorsTab caseStudies={[caseStudy]} clientName="TestCo" />);
    expect(screen.getByText(/Found 1 relevant competitor case stud/)).toBeTruthy();
  });

  it('renders plural count for multiple case studies', () => {
    render(<CompetitorsTab caseStudies={[caseStudy, caseStudy2]} clientName="TestCo" />);
    expect(screen.getByText(/Found 2 relevant competitor case stud/)).toBeTruthy();
  });

  // --- 2. Competitor details ---
  it('renders competitor name', () => {
    render(<CompetitorsTab caseStudies={[caseStudy]} clientName="TestCo" />);
    expect(screen.getByText('RivalCo')).toBeTruthy();
  });

  it('renders case study title', () => {
    render(<CompetitorsTab caseStudies={[caseStudy]} clientName="TestCo" />);
    expect(screen.getByText('AI-Powered Demand Forecasting')).toBeTruthy();
  });

  it('renders summary text', () => {
    render(<CompetitorsTab caseStudies={[caseStudy]} clientName="TestCo" />);
    expect(screen.getByText('RivalCo deployed ML to reduce overstock by 25%.')).toBeTruthy();
  });

  // --- 3. Relevance score badge ---
  it('renders relevance score as percentage', () => {
    render(<CompetitorsTab caseStudies={[caseStudy]} clientName="TestCo" />);
    expect(screen.getByText('90% match')).toBeTruthy();
  });

  it('renders 75% match for relevance_score=0.75', () => {
    render(<CompetitorsTab caseStudies={[caseStudy2]} clientName="TestCo" />);
    expect(screen.getByText('75% match')).toBeTruthy();
  });

  // --- 4. Technologies ---
  it('renders technologies_used badges', () => {
    render(<CompetitorsTab caseStudies={[caseStudy]} clientName="TestCo" />);
    expect(screen.getByText('Python')).toBeTruthy();
    expect(screen.getByText('TensorFlow')).toBeTruthy();
    expect(screen.getByText('Snowflake')).toBeTruthy();
  });

  it('hides technologies section when array is empty', () => {
    const cs = { ...caseStudy, technologies_used: [] };
    render(<CompetitorsTab caseStudies={[cs]} clientName="TestCo" />);
    expect(screen.queryByText('Technologies:')).toBeNull();
  });

  // --- 5. Outcomes ---
  it('renders outcomes list', () => {
    render(<CompetitorsTab caseStudies={[caseStudy]} clientName="TestCo" />);
    expect(screen.getByText('25% overstock reduction')).toBeTruthy();
    expect(screen.getByText('$3M cost savings annually')).toBeTruthy();
  });

  it('hides outcomes section when array is empty', () => {
    const cs = { ...caseStudy, outcomes: [] };
    render(<CompetitorsTab caseStudies={[cs]} clientName="TestCo" />);
    expect(screen.queryByText('Outcomes:')).toBeNull();
  });

  // --- 6. Multiple case studies render ---
  it('renders multiple case studies', () => {
    render(<CompetitorsTab caseStudies={[caseStudy, caseStudy2]} clientName="TestCo" />);
    expect(screen.getByText('RivalCo')).toBeTruthy();
    expect(screen.getByText('CompetitorB')).toBeTruthy();
    expect(screen.getByText('Cloud Migration at Scale')).toBeTruthy();
  });

  // --- 7. Empty array ---
  it('renders zero count message for empty array', () => {
    render(<CompetitorsTab caseStudies={[]} clientName="TestCo" />);
    expect(screen.getByText(/Found 0 relevant competitor case stud/)).toBeTruthy();
  });

  // --- 8. No crash without optional props ---
  it('renders without crashing when projectId/iterationId are absent', () => {
    const { container } = render(<CompetitorsTab caseStudies={[caseStudy]} clientName="TestCo" />);
    expect(container).toBeTruthy();
  });
});
