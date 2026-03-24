import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import GapsTab from '@/components/research-results/tabs/GapsTab';
import { GapAnalysis, WebSource } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const sources: WebSource[] = [
  { uri: 'https://source1.com', title: 'Source One' },
];

const fullGaps: GapAnalysis = {
  id: 'g1',
  technology_gaps: ['No SIEM deployed', 'Legacy ERP on SAP 4.6C'],
  capability_gaps: ['No cloud-native DevOps practice'],
  process_gaps: ['Manual patching process'],
  recommendations: ['Deploy Microsoft Sentinel for SIEM coverage'],
  priority_areas: ['Modernise security operations centre'],
  confidence_score: 0.82,
  analysis_notes: 'Based on job postings and LinkedIn data.',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const minimalGaps: GapAnalysis = {
  id: 'g2',
  technology_gaps: [],
  capability_gaps: [],
  process_gaps: [],
  recommendations: [],
  priority_areas: [],
  confidence_score: 0.5,
  analysis_notes: '',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const parsingFailureGaps: GapAnalysis = {
  ...minimalGaps,
  id: 'g3',
  analysis_notes: 'Analysis parsing failed — raw output stored.',
};

describe('GapsTab', () => {
  // --- 1. Parsing failure banner ---
  it('shows parsing failure banner when analysis_notes starts with failure text and all arrays empty', () => {
    render(<GapsTab gaps={parsingFailureGaps} clientName="TestCo" />);
    expect(screen.getByText('Gap analysis could not be parsed for this research job.')).toBeTruthy();
  });

  // --- 2. Normal render does not show failure banner ---
  it('does not show failure banner for a valid gaps object', () => {
    render(<GapsTab gaps={fullGaps} clientName="TestCo" />);
    expect(screen.queryByText('Gap analysis could not be parsed for this research job.')).toBeNull();
  });

  // --- 3. Confidence score ---
  it('renders confidence score as percentage', () => {
    render(<GapsTab gaps={fullGaps} clientName="TestCo" />);
    expect(screen.getByText('82%')).toBeTruthy();
    expect(screen.getByText('Analysis Confidence')).toBeTruthy();
  });

  // --- 4. Priority areas ---
  it('renders priority areas', () => {
    render(<GapsTab gaps={fullGaps} clientName="TestCo" />);
    expect(screen.getByText('Priority Areas')).toBeTruthy();
    expect(screen.getByText('Modernise security operations centre')).toBeTruthy();
  });

  // --- 5. Technology gaps ---
  it('renders technology gaps section', () => {
    render(<GapsTab gaps={fullGaps} clientName="TestCo" sources={sources} />);
    expect(screen.getByText('Technology Gaps')).toBeTruthy();
    expect(screen.getByText('No SIEM deployed')).toBeTruthy();
    expect(screen.getByText('Legacy ERP on SAP 4.6C')).toBeTruthy();
  });

  // --- 6. Capability gaps ---
  it('renders capability gaps section', () => {
    render(<GapsTab gaps={fullGaps} clientName="TestCo" />);
    expect(screen.getByText('Capability Gaps')).toBeTruthy();
    expect(screen.getByText('No cloud-native DevOps practice')).toBeTruthy();
  });

  // --- 7. Process gaps ---
  it('renders process gaps section', () => {
    render(<GapsTab gaps={fullGaps} clientName="TestCo" />);
    expect(screen.getByText('Process Gaps')).toBeTruthy();
    expect(screen.getByText('Manual patching process')).toBeTruthy();
  });

  // --- 8. Recommendations ---
  it('renders recommendations section', () => {
    render(<GapsTab gaps={fullGaps} clientName="TestCo" />);
    expect(screen.getByText('Recommendations')).toBeTruthy();
    expect(screen.getByText('Deploy Microsoft Sentinel for SIEM coverage')).toBeTruthy();
  });

  // --- 9. Analysis notes ---
  it('renders analysis notes', () => {
    render(<GapsTab gaps={fullGaps} clientName="TestCo" />);
    expect(screen.getByText('Analysis Notes')).toBeTruthy();
    expect(screen.getByText('Based on job postings and LinkedIn data.')).toBeTruthy();
  });

  // --- 10. Empty arrays hide sections ---
  it('hides gap sections when arrays are empty', () => {
    render(<GapsTab gaps={minimalGaps} clientName="TestCo" />);
    expect(screen.queryByText('Technology Gaps')).toBeNull();
    expect(screen.queryByText('Capability Gaps')).toBeNull();
    expect(screen.queryByText('Process Gaps')).toBeNull();
    expect(screen.queryByText('Recommendations')).toBeNull();
    expect(screen.queryByText('Priority Areas')).toBeNull();
  });

  // --- 11. Low confidence score renders red ---
  it('renders low confidence score', () => {
    const lowConf = { ...fullGaps, confidence_score: 0.2 };
    render(<GapsTab gaps={lowConf} clientName="TestCo" />);
    expect(screen.getByText('20%')).toBeTruthy();
  });

  // --- 12. No crash without optional props ---
  it('renders without crash when sources and project props are omitted', () => {
    const { container } = render(<GapsTab gaps={fullGaps} clientName="TestCo" />);
    expect(container).toBeTruthy();
  });
});
