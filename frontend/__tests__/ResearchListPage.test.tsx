import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ResearchListPage from '@/app/research/page';
import { ResearchJob } from '@/types';

vi.mock('@/lib/api', () => ({
  api: {
    listResearch: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/research',
}));

import { api } from '@/lib/api';

const mockApi = api as { listResearch: ReturnType<typeof vi.fn> };

const job: ResearchJob = {
  id: 'j1',
  client_name: 'Acme Corp',
  vertical: 'retail',
  status: 'completed',
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:00:00Z',
  website: '',
  prompt: '',
  sales_history: '',
  report: null,
  internal_ops: null,
  gap_analysis: null,
  starred: false,
  project: null,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ResearchListPage', () => {
  it('shows loading spinner initially', () => {
    mockApi.listResearch.mockReturnValue(new Promise(() => {}));
    render(<ResearchListPage />);
    expect(document.querySelector('.animate-spin')).toBeTruthy();
  });

  it('shows empty state when no jobs', async () => {
    mockApi.listResearch.mockResolvedValue([]);
    render(<ResearchListPage />);
    await waitFor(() => {
      expect(screen.getByText(/No research jobs yet/)).toBeTruthy();
    });
  });

  it('renders job list with client names', async () => {
    mockApi.listResearch.mockResolvedValue([job]);
    render(<ResearchListPage />);
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeTruthy();
    });
  });

  it('shows job count', async () => {
    mockApi.listResearch.mockResolvedValue([job]);
    render(<ResearchListPage />);
    await waitFor(() => {
      expect(screen.getByText('1 research job')).toBeTruthy();
    });
  });

  it('shows plural job count for multiple jobs', async () => {
    const job2 = { ...job, id: 'j2', client_name: 'Beta Inc' };
    mockApi.listResearch.mockResolvedValue([job, job2]);
    render(<ResearchListPage />);
    await waitFor(() => {
      expect(screen.getByText('2 research jobs')).toBeTruthy();
    });
  });

  it('shows status badge for each job', async () => {
    mockApi.listResearch.mockResolvedValue([job]);
    render(<ResearchListPage />);
    await waitFor(() => {
      expect(screen.getByText('completed')).toBeTruthy();
    });
  });

  it('shows vertical when present', async () => {
    mockApi.listResearch.mockResolvedValue([job]);
    render(<ResearchListPage />);
    await waitFor(() => {
      expect(screen.getByText('retail')).toBeTruthy();
    });
  });

  it('shows "New Research" button', async () => {
    mockApi.listResearch.mockResolvedValue([]);
    render(<ResearchListPage />);
    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'New Research' })).toBeTruthy();
    });
  });
});
