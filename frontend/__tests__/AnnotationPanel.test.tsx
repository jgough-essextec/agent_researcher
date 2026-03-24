import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AnnotationPanel from '@/components/projects/AnnotationPanel';
import { Annotation } from '@/types';

const mockUpdateAnnotation = vi.fn();
const mockDeleteAnnotation = vi.fn();

vi.mock('@/lib/api', () => ({
  api: {
    updateAnnotation: (projectId: string, id: string, data: object) =>
      mockUpdateAnnotation(projectId, id, data),
    deleteAnnotation: (projectId: string, id: string) =>
      mockDeleteAnnotation(projectId, id),
  },
}));

const annotations: Annotation[] = [
  {
    id: 'a1',
    project: 'p1',
    content_type: 'researchreport',
    content_type_name: 'Research Report',
    object_id: 'obj1',
    text: 'Follow up on the ERP discussion.',
    created_at: '2026-01-10T10:00:00Z',
    updated_at: '2026-01-10T10:00:00Z',
  },
];

describe('AnnotationPanel', () => {
  beforeEach(() => {
    mockUpdateAnnotation.mockResolvedValue({});
    mockDeleteAnnotation.mockResolvedValue({});
  });

  // --- 1. Renders annotation text ---
  it('renders existing annotation text', () => {
    render(<AnnotationPanel projectId="p1" annotations={annotations} onUpdate={() => {}} />);
    expect(screen.getByText('Follow up on the ERP discussion.')).toBeTruthy();
  });

  // --- 2. Empty state ---
  it('shows empty state when no annotations', () => {
    render(<AnnotationPanel projectId="p1" annotations={[]} onUpdate={() => {}} />);
    expect(screen.getByText('No notes yet')).toBeTruthy();
  });

  // --- 3. Edit buttons visible (icon-only SVG buttons) ---
  it('renders two icon buttons (edit + delete) per annotation', () => {
    render(<AnnotationPanel projectId="p1" annotations={annotations} onUpdate={() => {}} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBe(2);
  });

  // --- 4. Edit mode shows textarea ---
  it('clicking first button (edit) shows textarea with annotation text', () => {
    render(<AnnotationPanel projectId="p1" annotations={annotations} onUpdate={() => {}} />);
    const [editBtn] = screen.getAllByRole('button');
    fireEvent.click(editBtn);
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toBe('Follow up on the ERP discussion.');
  });

  // --- 5. Cancel exits edit mode ---
  it('Cancel button exits edit mode', () => {
    render(<AnnotationPanel projectId="p1" annotations={annotations} onUpdate={() => {}} />);
    fireEvent.click(screen.getAllByRole('button')[0]);
    fireEvent.click(screen.getByText('Cancel'));
    expect(screen.queryByRole('textbox')).toBeNull();
  });

  // --- 6. Save calls updateAnnotation ---
  it('Save button calls updateAnnotation with edited text', async () => {
    const onUpdate = vi.fn();
    render(<AnnotationPanel projectId="p1" annotations={annotations} onUpdate={onUpdate} />);
    fireEvent.click(screen.getAllByRole('button')[0]);
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'Updated note' } });
    fireEvent.click(screen.getByText('Save'));
    await waitFor(() => {
      expect(mockUpdateAnnotation).toHaveBeenCalledWith('p1', 'a1', { text: 'Updated note' });
      expect(onUpdate).toHaveBeenCalled();
    });
  });

  // --- 7. Delete calls deleteAnnotation ---
  it('clicking second button (delete) calls deleteAnnotation', async () => {
    const onUpdate = vi.fn();
    render(<AnnotationPanel projectId="p1" annotations={annotations} onUpdate={onUpdate} />);
    const [, deleteBtn] = screen.getAllByRole('button');
    fireEvent.click(deleteBtn);
    await waitFor(() => {
      expect(mockDeleteAnnotation).toHaveBeenCalledWith('p1', 'a1');
      expect(onUpdate).toHaveBeenCalled();
    });
  });
});
