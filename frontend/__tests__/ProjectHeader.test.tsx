import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ProjectHeader from '@/components/projects/ProjectHeader';
import { Project } from '@/types';

const mockUpdateProject = vi.fn();
vi.mock('@/lib/api', () => ({
  api: {
    updateProject: (id: string, data: object) => mockUpdateProject(id, data),
  },
}));

const baseProject: Project = {
  id: 'p1',
  name: 'Acme Deep Dive',
  client_name: 'Acme Corp',
  description: 'Strategic account research',
  context_mode: 'accumulate',
  iteration_count: 3,
  iterations: [{ id: 'i1', sequence: 1, status: 'completed', has_research_job: true, created_at: '2026-01-01T00:00:00Z' }],
  work_products_count: 5,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-03-01T00:00:00Z',
};

describe('ProjectHeader', () => {
  beforeEach(() => {
    mockUpdateProject.mockResolvedValue({ ...baseProject, context_mode: 'fresh' });
  });

  it('renders project name and client name', () => {
    render(<ProjectHeader project={baseProject} onUpdate={() => {}} />);
    expect(screen.getByText('Acme Deep Dive')).toBeTruthy();
    expect(screen.getByText('Acme Corp')).toBeTruthy();
  });

  it('renders optional description', () => {
    render(<ProjectHeader project={baseProject} onUpdate={() => {}} />);
    expect(screen.getByText('Strategic account research')).toBeTruthy();
  });

  it('does not render description when absent', () => {
    const project = { ...baseProject, description: undefined };
    render(<ProjectHeader project={project} onUpdate={() => {}} />);
    expect(screen.queryByText('Strategic account research')).toBeNull();
  });

  it('renders Build and Fresh context mode buttons', () => {
    render(<ProjectHeader project={baseProject} onUpdate={() => {}} />);
    expect(screen.getByRole('button', { name: 'Build' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Fresh' })).toBeTruthy();
  });

  it('highlights the active context mode button', () => {
    render(<ProjectHeader project={baseProject} onUpdate={() => {}} />);
    const buildBtn = screen.getByRole('button', { name: 'Build' });
    expect(buildBtn.className).toContain('purple');
  });

  it('calls api.updateProject and onUpdate when context mode is changed', async () => {
    const onUpdate = vi.fn();
    render(<ProjectHeader project={baseProject} onUpdate={onUpdate} />);
    fireEvent.click(screen.getByRole('button', { name: 'Fresh' }));
    await waitFor(() => {
      expect(mockUpdateProject).toHaveBeenCalledWith('p1', { context_mode: 'fresh' });
      expect(onUpdate).toHaveBeenCalled();
    });
  });

  it('renders iteration count and saved items count', () => {
    render(<ProjectHeader project={baseProject} onUpdate={() => {}} />);
    expect(screen.getByText('1 iterations')).toBeTruthy();
    expect(screen.getByText('5 saved items')).toBeTruthy();
  });
});
