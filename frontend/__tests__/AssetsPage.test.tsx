import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import AssetsPage from '@/app/assets/page';
import { ResearchJob, UseCase } from '@/types';

vi.mock('@/lib/api', () => ({
  api: {
    listResearch: vi.fn(),
    listUseCases: vi.fn(),
    listPersonas: vi.fn(),
    listOnePagers: vi.fn(),
    listAccountPlans: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/assets',
}));

import { api } from '@/lib/api';

const mockApi = api as {
  listResearch: ReturnType<typeof vi.fn>;
  listUseCases: ReturnType<typeof vi.fn>;
  listPersonas: ReturnType<typeof vi.fn>;
  listOnePagers: ReturnType<typeof vi.fn>;
  listAccountPlans: ReturnType<typeof vi.fn>;
};

const completedJob: ResearchJob = {
  id: 'j1',
  client_name: 'Acme Corp',
  vertical: 'retail',
  status: 'completed',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  website: '',
  prompt: '',
  sales_history: '',
  report: null,
  internal_ops: null,
  gap_analysis: null,
  starred: false,
  project: null,
};

const useCase: UseCase = {
  id: 'uc1',
  research_job: 'j1',
  title: 'AI Supply Chain',
  description: 'AI-driven supply chain optimization',
  business_problem: 'High costs',
  proposed_solution: 'ML pipeline',
  expected_benefits: [],
  estimated_roi: '$1M',
  time_to_value: '6 months',
  technologies: [],
  data_requirements: [],
  integration_points: [],
  priority: 'high',
  impact_score: 0.8,
  feasibility_score: 0.7,
  status: 'draft',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
  mockApi.listUseCases.mockResolvedValue([]);
  mockApi.listPersonas.mockResolvedValue([]);
  mockApi.listOnePagers.mockResolvedValue([]);
  mockApi.listAccountPlans.mockResolvedValue([]);
});

describe('AssetsPage', () => {
  it('shows loading spinner initially', () => {
    mockApi.listResearch.mockReturnValue(new Promise(() => {}));
    render(<AssetsPage />);
    expect(document.querySelector('.animate-spin')).toBeTruthy();
  });

  it('shows empty state when no completed jobs', async () => {
    mockApi.listResearch.mockResolvedValue([]);
    render(<AssetsPage />);
    await waitFor(() => {
      expect(screen.getByText('No completed research jobs yet. Generated assets will appear here.')).toBeTruthy();
    });
  });

  it('filters out non-completed jobs', async () => {
    const runningJob = { ...completedJob, id: 'j2', client_name: 'Beta Corp', status: 'running' as const };
    mockApi.listResearch.mockResolvedValue([completedJob, runningJob]);
    render(<AssetsPage />);
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeTruthy();
      expect(screen.queryByText('Beta Corp')).toBeNull();
    });
  });

  it('renders asset type filter buttons', async () => {
    mockApi.listResearch.mockResolvedValue([completedJob]);
    render(<AssetsPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Use Cases' })).toBeTruthy();
      expect(screen.getByRole('button', { name: 'Personas' })).toBeTruthy();
      expect(screen.getByRole('button', { name: 'One-Pagers' })).toBeTruthy();
      expect(screen.getByRole('button', { name: 'Account Plans' })).toBeTruthy();
    });
  });

  it('shows job client name in expandable list', async () => {
    mockApi.listResearch.mockResolvedValue([completedJob]);
    render(<AssetsPage />);
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeTruthy();
    });
  });

  it('loads assets when job is expanded', async () => {
    mockApi.listResearch.mockResolvedValue([completedJob]);
    mockApi.listUseCases.mockResolvedValue([useCase]);
    render(<AssetsPage />);
    await waitFor(() => screen.getByText('Acme Corp'));
    fireEvent.click(screen.getByText('Acme Corp').closest('button')!);
    await waitFor(() => {
      expect(mockApi.listUseCases).toHaveBeenCalledWith('j1');
    });
  });

  it('renders use case titles when expanded', async () => {
    mockApi.listResearch.mockResolvedValue([completedJob]);
    mockApi.listUseCases.mockResolvedValue([useCase]);
    render(<AssetsPage />);
    await waitFor(() => screen.getByText('Acme Corp'));
    fireEvent.click(screen.getByText('Acme Corp').closest('button')!);
    await waitFor(() => {
      expect(screen.getByText('AI Supply Chain')).toBeTruthy();
    });
  });

  it('shows "Assets" heading', async () => {
    mockApi.listResearch.mockResolvedValue([completedJob]);
    render(<AssetsPage />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Assets' })).toBeTruthy();
    });
  });

  it('shows job count', async () => {
    mockApi.listResearch.mockResolvedValue([completedJob]);
    render(<AssetsPage />);
    await waitFor(() => {
      expect(screen.getByText(/1 completed research job/)).toBeTruthy();
    });
  });
});
