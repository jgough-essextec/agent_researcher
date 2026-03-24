import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import IterationTimeline from '@/components/projects/IterationTimeline';
import { IterationListItem } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const iterations: IterationListItem[] = [
  {
    id: 'i1',
    sequence: 1,
    name: 'Q1 Research',
    status: 'completed',
    has_research_job: true,
    created_at: '2026-01-10T00:00:00Z',
  },
  {
    id: 'i2',
    sequence: 2,
    name: undefined,
    status: 'running',
    has_research_job: false,
    created_at: '2026-02-15T00:00:00Z',
  },
];

describe('IterationTimeline', () => {
  it('shows empty state when iterations is empty', () => {
    render(<IterationTimeline iterations={[]} onSelect={() => {}} />);
    expect(screen.getByText('No iterations yet')).toBeTruthy();
  });

  it('renders iteration names', () => {
    render(<IterationTimeline iterations={iterations} selectedSequence={1} onSelect={() => {}} />);
    expect(screen.getByText('Q1 Research')).toBeTruthy();
  });

  it('falls back to "Iteration N" when name is absent', () => {
    render(<IterationTimeline iterations={iterations} selectedSequence={1} onSelect={() => {}} />);
    expect(screen.getByText('Iteration 2')).toBeTruthy();
  });

  it('calls onSelect with the correct sequence on click', () => {
    const onSelect = vi.fn();
    render(<IterationTimeline iterations={iterations} selectedSequence={1} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('Iteration 2'));
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  it('renders a formatted date for each iteration', () => {
    render(<IterationTimeline iterations={iterations} selectedSequence={1} onSelect={() => {}} />);
    // Jan 10 date
    expect(screen.getByText(/Jan/)).toBeTruthy();
  });

  it('does not crash without selectedSequence', () => {
    const { container } = render(
      <IterationTimeline iterations={iterations} onSelect={() => {}} />
    );
    expect(container).toBeTruthy();
  });
});
