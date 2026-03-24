import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GenerateTab from '@/components/research-results/tabs/GenerateTab';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockAddToast = vi.fn().mockReturnValue('toast-id');
const mockRemoveToast = vi.fn();

vi.mock('@/lib/toast', () => ({
  useToast: () => ({
    addToast: mockAddToast,
    removeToast: mockRemoveToast,
  }),
}));

const mockListUseCases = vi.fn();
const mockListPersonas = vi.fn();
const mockListOnePagers = vi.fn();
const mockListAccountPlans = vi.fn();
const mockGenerateUseCases = vi.fn();
const mockGeneratePersonas = vi.fn();
const mockGenerateOnePager = vi.fn();
const mockGenerateAccountPlan = vi.fn();

vi.mock('@/lib/api', () => ({
  api: {
    listUseCases: (...args: unknown[]) => mockListUseCases(...args),
    listPersonas: (...args: unknown[]) => mockListPersonas(...args),
    listOnePagers: (...args: unknown[]) => mockListOnePagers(...args),
    listAccountPlans: (...args: unknown[]) => mockListAccountPlans(...args),
    generateUseCases: (...args: unknown[]) => mockGenerateUseCases(...args),
    generatePersonas: (...args: unknown[]) => mockGeneratePersonas(...args),
    generateOnePager: (...args: unknown[]) => mockGenerateOnePager(...args),
    generateAccountPlan: (...args: unknown[]) => mockGenerateAccountPlan(...args),
  },
}));

// Minimal child section stubs to avoid deep rendering
vi.mock('@/components/research-results/generate/UseCaseSection', () => ({
  default: ({ useCases, generating, onGenerate }: { useCases: unknown[]; generating: boolean; onGenerate: () => void }) => (
    <div>
      <span data-testid="use-case-count">{useCases.length}</span>
      <button onClick={onGenerate} disabled={generating} data-testid="gen-use-cases">
        Generate Use Cases
      </button>
    </div>
  ),
}));

vi.mock('@/components/research-results/generate/PersonaSection', () => ({
  default: ({ personas, generating, onGenerate }: { personas: unknown[]; generating: boolean; onGenerate: () => void }) => (
    <div>
      <span data-testid="persona-count">{personas.length}</span>
      <button onClick={onGenerate} disabled={generating} data-testid="gen-personas">
        Generate Personas
      </button>
    </div>
  ),
}));

vi.mock('@/components/research-results/generate/OnePagerSection', () => ({
  default: ({ onePager, generating, onGenerate }: { onePager: unknown; generating: boolean; onGenerate: () => void }) => (
    <div>
      <span data-testid="one-pager-present">{onePager ? 'yes' : 'no'}</span>
      <button onClick={onGenerate} disabled={generating} data-testid="gen-one-pager">
        Generate One-Pager
      </button>
    </div>
  ),
}));

vi.mock('@/components/research-results/generate/AccountPlanSection', () => ({
  default: ({ accountPlan, generating, onGenerate }: { accountPlan: unknown; generating: boolean; onGenerate: () => void }) => (
    <div>
      <span data-testid="account-plan-present">{accountPlan ? 'yes' : 'no'}</span>
      <button onClick={onGenerate} disabled={generating} data-testid="gen-account-plan">
        Generate Account Plan
      </button>
    </div>
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resolveEmpty() {
  mockListUseCases.mockResolvedValue([]);
  mockListPersonas.mockResolvedValue([]);
  mockListOnePagers.mockResolvedValue([]);
  mockListAccountPlans.mockResolvedValue([]);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('GenerateTab', () => {
  const JOB_ID = 'job-abc-123';

  beforeEach(() => {
    vi.clearAllMocks();
    resolveEmpty();
  });

  describe('load on mount', () => {
    it('shows spinner while loading', () => {
      // Keep promises pending
      mockListUseCases.mockReturnValue(new Promise(() => {}));
      mockListPersonas.mockReturnValue(new Promise(() => {}));
      mockListOnePagers.mockReturnValue(new Promise(() => {}));
      mockListAccountPlans.mockReturnValue(new Promise(() => {}));

      render(<GenerateTab researchJobId={JOB_ID} />);

      // The spinner SVG is rendered during load
      expect(document.querySelector('svg.animate-spin')).toBeTruthy();
    });

    it('calls all four list APIs on mount', async () => {
      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => {
        expect(mockListUseCases).toHaveBeenCalledWith(JOB_ID);
        expect(mockListPersonas).toHaveBeenCalledWith(JOB_ID);
        expect(mockListOnePagers).toHaveBeenCalledWith(JOB_ID);
        expect(mockListAccountPlans).toHaveBeenCalledWith(JOB_ID);
      });
    });

    it('hides spinner after load completes', async () => {
      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => {
        expect(document.querySelector('svg.animate-spin')).toBeNull();
      });
    });

    it('displays info banner after load', async () => {
      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => {
        expect(
          screen.getByText(/generate sales assets from your research/i)
        ).toBeInTheDocument();
      });
    });

    it('populates use cases from API response', async () => {
      mockListUseCases.mockResolvedValue([
        { id: 'uc1', title: 'UC 1' },
        { id: 'uc2', title: 'UC 2' },
      ]);

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => {
        expect(screen.getByTestId('use-case-count').textContent).toBe('2');
      });
    });

    it('populates personas from API response', async () => {
      mockListPersonas.mockResolvedValue([{ id: 'p1', name: 'Persona 1' }]);

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => {
        expect(screen.getByTestId('persona-count').textContent).toBe('1');
      });
    });

    it('populates one-pager from first result in list', async () => {
      mockListOnePagers.mockResolvedValue([{ id: 'op1', title: 'One Pager' }]);

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => {
        expect(screen.getByTestId('one-pager-present').textContent).toBe('yes');
      });
    });

    it('populates account plan from first result in list', async () => {
      mockListAccountPlans.mockResolvedValue([{ id: 'ap1', title: 'Account Plan' }]);

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => {
        expect(screen.getByTestId('account-plan-present').textContent).toBe('yes');
      });
    });

    it('handles partial API failures gracefully — failed calls do not crash', async () => {
      mockListUseCases.mockRejectedValue(new Error('Network error'));
      mockListPersonas.mockResolvedValue([{ id: 'p1', name: 'Alice' }]);

      render(<GenerateTab researchJobId={JOB_ID} />);

      // Should still render (use cases empty, personas populated)
      await waitFor(() => {
        expect(screen.getByTestId('use-case-count').textContent).toBe('0');
        expect(screen.getByTestId('persona-count').textContent).toBe('1');
      });
    });
  });

  describe('generate use cases', () => {
    it('calls generateUseCases with the job ID', async () => {
      mockGenerateUseCases.mockResolvedValue([{ id: 'uc1', title: 'UC 1' }]);
      const user = userEvent.setup();

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => screen.getByTestId('gen-use-cases'));

      await user.click(screen.getByTestId('gen-use-cases'));

      await waitFor(() => {
        expect(mockGenerateUseCases).toHaveBeenCalledWith(JOB_ID);
      });
    });

    it('updates use case count after generation', async () => {
      mockGenerateUseCases.mockResolvedValue([
        { id: 'uc1', title: 'UC 1' },
        { id: 'uc2', title: 'UC 2' },
        { id: 'uc3', title: 'UC 3' },
      ]);
      const user = userEvent.setup();

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => screen.getByTestId('gen-use-cases'));

      await user.click(screen.getByTestId('gen-use-cases'));

      await waitFor(() => {
        expect(screen.getByTestId('use-case-count').textContent).toBe('3');
      });
    });

    it('shows loading toast while generating', async () => {
      mockGenerateUseCases.mockReturnValue(new Promise(() => {})); // keep pending
      const user = userEvent.setup();

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => screen.getByTestId('gen-use-cases'));

      await user.click(screen.getByTestId('gen-use-cases'));

      expect(mockAddToast).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'loading', message: expect.stringContaining('use cases') })
      );
    });

    it('shows error toast when generation fails', async () => {
      mockGenerateUseCases.mockRejectedValue(new Error('Server error'));
      const user = userEvent.setup();

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => screen.getByTestId('gen-use-cases'));

      await user.click(screen.getByTestId('gen-use-cases'));

      await waitFor(() => {
        expect(mockAddToast).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'error' })
        );
      });
    });
  });

  describe('generate account plan', () => {
    it('calls generateAccountPlan with the job ID', async () => {
      mockGenerateAccountPlan.mockResolvedValue({ id: 'ap1', title: 'Plan' });
      const user = userEvent.setup();

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => screen.getByTestId('gen-account-plan'));

      await user.click(screen.getByTestId('gen-account-plan'));

      await waitFor(() => {
        expect(mockGenerateAccountPlan).toHaveBeenCalledWith(JOB_ID);
      });
    });

    it('sets account plan after successful generation', async () => {
      mockGenerateAccountPlan.mockResolvedValue({ id: 'ap1', title: 'New Plan' });
      const user = userEvent.setup();

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => screen.getByTestId('gen-account-plan'));
      expect(screen.getByTestId('account-plan-present').textContent).toBe('no');

      await user.click(screen.getByTestId('gen-account-plan'));

      await waitFor(() => {
        expect(screen.getByTestId('account-plan-present').textContent).toBe('yes');
      });
    });

    it('shows error toast when account plan generation fails', async () => {
      mockGenerateAccountPlan.mockRejectedValue(new Error('Gemini error'));
      const user = userEvent.setup();

      render(<GenerateTab researchJobId={JOB_ID} />);

      await waitFor(() => screen.getByTestId('gen-account-plan'));

      await user.click(screen.getByTestId('gen-account-plan'));

      await waitFor(() => {
        expect(mockAddToast).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'error', message: expect.stringContaining('account plan') })
        );
      });
    });
  });
});
