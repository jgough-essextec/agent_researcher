import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import WorkProductPanel from '@/components/projects/WorkProductPanel';
import { WorkProduct } from '@/types';

const mockDeleteWorkProduct = vi.fn();

vi.mock('@/lib/api', () => ({
  api: {
    deleteWorkProduct: (projectId: string, id: string) => mockDeleteWorkProduct(projectId, id),
  },
}));

const workProducts: WorkProduct[] = [
  {
    id: 'wp1',
    project: 'p1',
    content_type: 'researchreport',
    content_type_name: 'Research Report',
    object_id: 'obj1',
    category: 'insight',
    starred: true,
    notes: 'Key finding about ERP gaps.',
    source_iteration_sequence: 2,
    content_preview: {
      title: 'ERP Gap Insight',
      summary: 'Acme has no unified ERP platform.',
    },
    created_at: '2026-01-10T00:00:00Z',
  },
  {
    id: 'wp2',
    project: 'p1',
    content_type: 'persona',
    content_type_name: 'Persona',
    object_id: 'obj2',
    category: 'persona',
    starred: true,
    notes: '',
    source_iteration_sequence: 1,
    content_preview: undefined,
    created_at: '2026-01-11T00:00:00Z',
  },
];

describe('WorkProductPanel', () => {
  beforeEach(() => {
    mockDeleteWorkProduct.mockResolvedValue({});
  });

  it('shows empty state when no work products', () => {
    render(<WorkProductPanel projectId="p1" workProducts={[]} onUpdate={() => {}} />);
    expect(screen.getByText('No starred items yet')).toBeTruthy();
  });

  it('renders work product title from content_preview', () => {
    render(<WorkProductPanel projectId="p1" workProducts={workProducts} onUpdate={() => {}} />);
    expect(screen.getByText('ERP Gap Insight')).toBeTruthy();
  });

  it('falls back to category name when content_preview has no title', () => {
    render(<WorkProductPanel projectId="p1" workProducts={workProducts} onUpdate={() => {}} />);
    expect(screen.getByText('persona')).toBeTruthy();
  });

  it('renders source iteration sequence', () => {
    render(<WorkProductPanel projectId="p1" workProducts={workProducts} onUpdate={() => {}} />);
    expect(screen.getByText('From iteration 2')).toBeTruthy();
    expect(screen.getByText('From iteration 1')).toBeTruthy();
  });

  it('clicking a work product row expands to show summary', () => {
    render(<WorkProductPanel projectId="p1" workProducts={workProducts} onUpdate={() => {}} />);
    fireEvent.click(screen.getByText('ERP Gap Insight').closest('div[class*="cursor-pointer"]')!);
    expect(screen.getByText('Acme has no unified ERP platform.')).toBeTruthy();
  });

  it('clicking expanded row collapses summary', () => {
    render(<WorkProductPanel projectId="p1" workProducts={workProducts} onUpdate={() => {}} />);
    const row = screen.getByText('ERP Gap Insight').closest('div[class*="cursor-pointer"]')!;
    fireEvent.click(row);
    fireEvent.click(row);
    expect(screen.queryByText('Acme has no unified ERP platform.')).toBeNull();
  });

  it('clicking expand also shows notes', () => {
    render(<WorkProductPanel projectId="p1" workProducts={workProducts} onUpdate={() => {}} />);
    fireEvent.click(screen.getByText('ERP Gap Insight').closest('div[class*="cursor-pointer"]')!);
    expect(screen.getByText('Key finding about ERP gaps.')).toBeTruthy();
  });

  it('remove button calls deleteWorkProduct and onUpdate', async () => {
    const onUpdate = vi.fn();
    render(<WorkProductPanel projectId="p1" workProducts={workProducts} onUpdate={onUpdate} />);
    const removeButtons = screen.getAllByRole('button');
    fireEvent.click(removeButtons[0]);
    await waitFor(() => {
      expect(mockDeleteWorkProduct).toHaveBeenCalledWith('p1', 'wp1');
      expect(onUpdate).toHaveBeenCalled();
    });
  });

  it('remove button does not trigger row expansion (stopPropagation)', async () => {
    render(<WorkProductPanel projectId="p1" workProducts={workProducts} onUpdate={() => {}} />);
    const removeButtons = screen.getAllByRole('button');
    fireEvent.click(removeButtons[0]);
    await waitFor(() => expect(mockDeleteWorkProduct).toHaveBeenCalled());
    expect(screen.queryByText('Acme has no unified ERP platform.')).toBeNull();
  });
});
