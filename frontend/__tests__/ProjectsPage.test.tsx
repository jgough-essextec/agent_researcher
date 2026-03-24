import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ProjectsPage from '@/app/projects/page';
import { ProjectListItem } from '@/types';

vi.mock('@/lib/api', () => ({
  api: {
    listProjects: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/projects',
}));

import { api } from '@/lib/api';

const mockApi = api as { listProjects: ReturnType<typeof vi.fn> };

const project: ProjectListItem = {
  id: 'p1',
  name: 'Acme AI Initiative',
  client_name: 'Acme Corp',
  description: 'Cloud migration project',
  context_mode: 'accumulate',
  status: 'active',
  iteration_count: 3,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ProjectsPage', () => {
  it('shows loading spinner initially', () => {
    mockApi.listProjects.mockReturnValue(new Promise(() => {}));
    render(<ProjectsPage />);
    expect(document.querySelector('.animate-spin')).toBeTruthy();
  });

  it('shows empty state when no projects', async () => {
    mockApi.listProjects.mockResolvedValue([]);
    render(<ProjectsPage />);
    await waitFor(() => {
      expect(screen.getByText('No projects yet')).toBeTruthy();
    });
  });

  it('shows error state on API failure', async () => {
    mockApi.listProjects.mockRejectedValue(new Error('Network error'));
    render(<ProjectsPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load projects')).toBeTruthy();
    });
  });

  it('shows "Try Again" button on error', async () => {
    mockApi.listProjects.mockRejectedValue(new Error('Network error'));
    render(<ProjectsPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Try Again' })).toBeTruthy();
    });
  });

  it('retries on Try Again click', async () => {
    mockApi.listProjects.mockRejectedValueOnce(new Error('fail')).mockResolvedValue([]);
    render(<ProjectsPage />);
    await waitFor(() => screen.getByRole('button', { name: 'Try Again' }));
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }));
    expect(mockApi.listProjects).toHaveBeenCalledTimes(2);
  });

  it('renders project cards when projects exist', async () => {
    mockApi.listProjects.mockResolvedValue([project]);
    render(<ProjectsPage />);
    await waitFor(() => {
      expect(screen.getByText('Acme AI Initiative')).toBeTruthy();
    });
  });

  it('shows "New Project" button', async () => {
    mockApi.listProjects.mockResolvedValue([]);
    render(<ProjectsPage />);
    await waitFor(() => {
      expect(screen.getAllByRole('link', { name: /New Project|Create Project/ }).length).toBeGreaterThan(0);
    });
  });

  it('renders heading "Projects"', async () => {
    mockApi.listProjects.mockResolvedValue([]);
    render(<ProjectsPage />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Projects' })).toBeTruthy();
    });
  });
});
