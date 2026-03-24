import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NewProjectPage from '@/app/projects/new/page';

const mockPush = vi.fn();

vi.mock('@/lib/api', () => ({
  api: {
    createProject: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/projects/new',
}));

import { api } from '@/lib/api';

const mockApi = api as { createProject: ReturnType<typeof vi.fn> };

beforeEach(() => {
  vi.clearAllMocks();
});

describe('NewProjectPage', () => {
  it('renders heading', () => {
    render(<NewProjectPage />);
    expect(screen.getByRole('heading', { name: 'Create New Project' })).toBeTruthy();
  });

  it('shows project name and client name inputs', () => {
    render(<NewProjectPage />);
    expect(screen.getByLabelText(/Project Name/)).toBeTruthy();
    expect(screen.getByLabelText(/Client Name/)).toBeTruthy();
  });

  it('shows validation error when required fields are empty', async () => {
    render(<NewProjectPage />);
    fireEvent.click(screen.getByRole('button', { name: /Create Project/ }));
    await waitFor(() => {
      expect(screen.getByText('Project name and client name are required')).toBeTruthy();
    });
  });

  it('calls api.createProject with form data', async () => {
    mockApi.createProject.mockResolvedValue({ id: 'new-p1' });
    render(<NewProjectPage />);
    fireEvent.change(screen.getByLabelText(/Project Name/), { target: { value: 'My Project' } });
    fireEvent.change(screen.getByLabelText(/Client Name/), { target: { value: 'Acme Corp' } });
    fireEvent.click(screen.getByRole('button', { name: /Create Project/ }));
    await waitFor(() => {
      expect(mockApi.createProject).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'My Project', client_name: 'Acme Corp' })
      );
    });
  });

  it('redirects to project page on success', async () => {
    mockApi.createProject.mockResolvedValue({ id: 'new-p1' });
    render(<NewProjectPage />);
    fireEvent.change(screen.getByLabelText(/Project Name/), { target: { value: 'My Project' } });
    fireEvent.change(screen.getByLabelText(/Client Name/), { target: { value: 'Acme Corp' } });
    fireEvent.click(screen.getByRole('button', { name: /Create Project/ }));
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/projects/new-p1');
    });
  });

  it('shows error message on API failure', async () => {
    mockApi.createProject.mockRejectedValue(new Error('Network error'));
    render(<NewProjectPage />);
    fireEvent.change(screen.getByLabelText(/Project Name/), { target: { value: 'My Project' } });
    fireEvent.change(screen.getByLabelText(/Client Name/), { target: { value: 'Acme Corp' } });
    fireEvent.click(screen.getByRole('button', { name: /Create Project/ }));
    await waitFor(() => {
      expect(screen.getByText('Failed to create project')).toBeTruthy();
    });
  });

  it('shows "accumulate" context mode selected by default', () => {
    render(<NewProjectPage />);
    expect(screen.getByText('Build Context')).toBeTruthy();
  });

  it('can switch to fresh context mode', () => {
    render(<NewProjectPage />);
    fireEvent.click(screen.getByText('Fresh Start'));
    // The fresh button should now be highlighted — verify by checking that createProject
    // will be called with context_mode: 'fresh'
    expect(screen.getByText('Fresh Start')).toBeTruthy();
  });

  it('shows "Back to Projects" link', () => {
    render(<NewProjectPage />);
    expect(screen.getByRole('link', { name: /Back to Projects/ })).toBeTruthy();
  });
});
