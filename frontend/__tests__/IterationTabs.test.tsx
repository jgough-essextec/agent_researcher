import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import IterationTabs from '@/components/projects/IterationTabs';
import { IterationListItem } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const iterations: IterationListItem[] = [
  {
    id: 'i1',
    sequence: 1,
    name: 'Initial Research',
    status: 'completed',
    has_research_job: true,
    research_job_status: 'completed',
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'i2',
    sequence: 2,
    name: undefined,
    status: 'running',
    has_research_job: false,
    created_at: '2026-01-15T00:00:00Z',
  },
];

describe('IterationTabs', () => {
  it('renders nothing when iterations array is empty', () => {
    const { container } = render(
      <IterationTabs iterations={[]} onSelect={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders a button for each iteration', () => {
    render(<IterationTabs iterations={iterations} selectedSequence={1} onSelect={() => {}} />);
    expect(screen.getByText('Initial Research')).toBeTruthy();
    expect(screen.getByText('Iteration 2')).toBeTruthy();
  });

  it('falls back to "Iteration N" label when name is undefined', () => {
    render(<IterationTabs iterations={iterations} selectedSequence={1} onSelect={() => {}} />);
    expect(screen.getByText('Iteration 2')).toBeTruthy();
  });

  it('calls onSelect with the correct sequence on click', () => {
    const onSelect = vi.fn();
    render(<IterationTabs iterations={iterations} selectedSequence={1} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('Iteration 2'));
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  it('highlights the selected iteration tab', () => {
    render(<IterationTabs iterations={iterations} selectedSequence={1} onSelect={() => {}} />);
    const activeBtn = screen.getByText('Initial Research').closest('button');
    expect(activeBtn?.className).toContain('blue-500');
  });

  it('shows Compare button when there are 2+ iterations and onCompare is provided', () => {
    render(
      <IterationTabs
        iterations={iterations}
        selectedSequence={1}
        onSelect={() => {}}
        onCompare={() => {}}
      />
    );
    expect(screen.getByText('Compare')).toBeTruthy();
  });

  it('hides Compare button when onCompare is not provided', () => {
    render(
      <IterationTabs iterations={iterations} selectedSequence={1} onSelect={() => {}} />
    );
    expect(screen.queryByText('Compare')).toBeNull();
  });

  it('hides Compare button when only 1 iteration', () => {
    render(
      <IterationTabs
        iterations={[iterations[0]]}
        selectedSequence={1}
        onSelect={() => {}}
        onCompare={() => {}}
      />
    );
    expect(screen.queryByText('Compare')).toBeNull();
  });

  it('calls onCompare when Compare button is clicked', () => {
    const onCompare = vi.fn();
    render(
      <IterationTabs
        iterations={iterations}
        selectedSequence={1}
        onSelect={() => {}}
        onCompare={onCompare}
      />
    );
    fireEvent.click(screen.getByText('Compare'));
    expect(onCompare).toHaveBeenCalled();
  });

  it('shows research-complete checkmark for completed research job', () => {
    render(<IterationTabs iterations={iterations} selectedSequence={1} onSelect={() => {}} />);
    expect(screen.getByTitle('Research complete — assets available')).toBeTruthy();
  });
});
