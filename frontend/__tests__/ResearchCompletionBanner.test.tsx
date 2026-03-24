import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ResearchCompletionBanner from '@/components/ResearchCompletionBanner';

// ---------------------------------------------------------------------------
// localStorage helpers
// ---------------------------------------------------------------------------

const STORAGE_KEY = (jobId: string) => `banner_dismissed_${jobId}`;

function clearBannerStorage(jobId: string) {
  localStorage.removeItem(STORAGE_KEY(jobId));
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ResearchCompletionBanner', () => {
  const JOB_ID = 'job-test-123';
  const onOpenGenerate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    clearBannerStorage(JOB_ID);
  });

  describe('initial visibility', () => {
    it('renders banner when localStorage key is absent', () => {
      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      expect(screen.getByText(/research complete/i)).toBeInTheDocument();
    });

    it('does not render banner when dismissed key is "true" in localStorage', () => {
      localStorage.setItem(STORAGE_KEY(JOB_ID), 'true');

      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      expect(screen.queryByText(/research complete/i)).toBeNull();
    });

    it('renders banner when dismissed key is "false" in localStorage', () => {
      localStorage.setItem(STORAGE_KEY(JOB_ID), 'false');

      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      expect(screen.getByText(/research complete/i)).toBeInTheDocument();
    });
  });

  describe('dismiss button', () => {
    it('hides the banner when dismiss button is clicked', () => {
      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      const dismissBtn = screen.getByRole('button', { name: /dismiss/i });
      fireEvent.click(dismissBtn);

      expect(screen.queryByText(/research complete/i)).toBeNull();
    });

    it('persists dismissed state to localStorage on dismiss', () => {
      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      fireEvent.click(screen.getByRole('button', { name: /dismiss/i }));

      expect(localStorage.getItem(STORAGE_KEY(JOB_ID))).toBe('true');
    });

    it('uses the correct per-job storage key', () => {
      const OTHER_ID = 'job-other-999';
      clearBannerStorage(OTHER_ID);

      render(<ResearchCompletionBanner jobId={OTHER_ID} onOpenGenerate={onOpenGenerate} />);

      fireEvent.click(screen.getByRole('button', { name: /dismiss/i }));

      expect(localStorage.getItem(STORAGE_KEY(OTHER_ID))).toBe('true');
      // The original job's key should not be affected
      expect(localStorage.getItem(STORAGE_KEY(JOB_ID))).toBeNull();
    });
  });

  describe('generate assets button', () => {
    it('renders the "Generate Assets" button', () => {
      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      expect(screen.getByRole('button', { name: /generate assets/i })).toBeInTheDocument();
    });

    it('calls onOpenGenerate when "Generate Assets" is clicked', () => {
      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      fireEvent.click(screen.getByRole('button', { name: /generate assets/i }));

      expect(onOpenGenerate).toHaveBeenCalledTimes(1);
    });

    it('does not dismiss the banner when "Generate Assets" is clicked', () => {
      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      fireEvent.click(screen.getByRole('button', { name: /generate assets/i }));

      // Banner should still be visible
      expect(screen.getByText(/research complete/i)).toBeInTheDocument();
    });
  });

  describe('re-mount respects persisted state', () => {
    it('stays hidden after re-mount if previously dismissed', () => {
      const { unmount } = render(
        <ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />
      );

      fireEvent.click(screen.getByRole('button', { name: /dismiss/i }));
      unmount();

      render(<ResearchCompletionBanner jobId={JOB_ID} onOpenGenerate={onOpenGenerate} />);

      expect(screen.queryByText(/research complete/i)).toBeNull();
    });
  });

  describe('different job IDs are independent', () => {
    it('dismissing one job does not dismiss another', () => {
      const JOB_A = 'job-aaa';
      const JOB_B = 'job-bbb';
      clearBannerStorage(JOB_A);
      clearBannerStorage(JOB_B);

      const { unmount: unmountA } = render(
        <ResearchCompletionBanner jobId={JOB_A} onOpenGenerate={onOpenGenerate} />
      );
      fireEvent.click(screen.getByRole('button', { name: /dismiss/i }));
      unmountA();

      render(<ResearchCompletionBanner jobId={JOB_B} onOpenGenerate={onOpenGenerate} />);

      expect(screen.getByText(/research complete/i)).toBeInTheDocument();

      clearBannerStorage(JOB_A);
      clearBannerStorage(JOB_B);
    });
  });
});
