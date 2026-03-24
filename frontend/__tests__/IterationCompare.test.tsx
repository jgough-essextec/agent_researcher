import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import IterationCompare from '@/components/projects/IterationCompare';
import { IterationComparison } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const comparison: IterationComparison = {
  iteration_a: {
    id: 'i1',
    sequence: 1,
    name: 'Q1 Research',
    status: 'completed',
    created_at: '2026-01-01T00:00:00Z',
    report: {
      company_overview: 'Acme is a global firm.',
      pain_points: ['ERP fragmentation'],
      opportunities: ['Cloud migration'],
      digital_maturity: 'maturing',
      ai_adoption_stage: 'implementing',
      talking_points: ['How are you handling governance?'],
      decision_makers: [],
    },
  },
  iteration_b: {
    id: 'i2',
    sequence: 2,
    name: 'Q2 Research',
    status: 'completed',
    created_at: '2026-04-01T00:00:00Z',
    report: {
      company_overview: 'Acme is expanding.',
      pain_points: ['ERP fragmentation', 'Manual reporting'],
      opportunities: ['Cloud migration', 'AI adoption'],
      digital_maturity: 'advanced',
      ai_adoption_stage: 'scaling',
      talking_points: ['How are you handling governance?', 'New AI pilot?'],
      decision_makers: [],
    },
  },
  differences: {
    pain_points: {
      added: ['Manual reporting'],
      removed: [],
      unchanged: ['ERP fragmentation'],
    },
    opportunities: {
      added: ['AI adoption'],
      removed: [],
      unchanged: ['Cloud migration'],
    },
    talking_points: {
      added: ['New AI pilot?'],
      removed: [],
      unchanged: ['How are you handling governance?'],
    },
  },
};

describe('IterationCompare', () => {
  it('renders iteration names in the heading', () => {
    render(<IterationCompare comparison={comparison} onClose={() => {}} />);
    expect(screen.getByText('Q1 Research')).toBeTruthy();
    expect(screen.getByText('Q2 Research')).toBeTruthy();
  });

  it('renders added pain point', () => {
    render(<IterationCompare comparison={comparison} onClose={() => {}} />);
    expect(screen.getByText('Manual reporting')).toBeTruthy();
  });

  it('renders added opportunity', () => {
    render(<IterationCompare comparison={comparison} onClose={() => {}} />);
    expect(screen.getByText('AI adoption')).toBeTruthy();
  });

  it('renders added talking point', () => {
    render(<IterationCompare comparison={comparison} onClose={() => {}} />);
    expect(screen.getByText('New AI pilot?')).toBeTruthy();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<IterationCompare comparison={comparison} onClose={onClose} />);
    // Find a Close button (label may vary)
    const closeButtons = screen.getAllByRole('button');
    fireEvent.click(closeButtons[0]);
    expect(onClose).toHaveBeenCalled();
  });

  it('renders without crashing for empty diffs', () => {
    const emptyDiff = {
      ...comparison,
      differences: {
        pain_points: { added: [], removed: [], unchanged: [] },
        opportunities: { added: [], removed: [], unchanged: [] },
        talking_points: { added: [], removed: [], unchanged: [] },
      },
    };
    const { container } = render(<IterationCompare comparison={emptyDiff} onClose={() => {}} />);
    expect(container).toBeTruthy();
  });
});
