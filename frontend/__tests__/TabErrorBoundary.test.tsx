import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import TabErrorBoundary from '@/components/research-results/shared/TabErrorBoundary';

// A component that always throws during render
const ThrowingComponent = () => {
  throw new Error('Test crash');
};

describe('TabErrorBoundary', () => {
  it('renders children normally when no error occurs', () => {
    render(
      <TabErrorBoundary tabName="Test Tab">
        <div>Everything is fine</div>
      </TabErrorBoundary>
    );
    expect(screen.getByText('Everything is fine')).toBeTruthy();
  });

  it('renders fallback UI when child throws', () => {
    // Suppress the React error output to keep test output clean
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <TabErrorBoundary tabName="Org Signals">
        <ThrowingComponent />
      </TabErrorBoundary>
    );

    expect(screen.getByText(/something went wrong/i)).toBeTruthy();
    consoleSpy.mockRestore();
  });

  it('shows the tab name in the fallback UI', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <TabErrorBoundary tabName="Competitors">
        <ThrowingComponent />
      </TabErrorBoundary>
    );

    expect(screen.getByText(/Competitors/)).toBeTruthy();
    consoleSpy.mockRestore();
  });

  it('renders a retry/reset button in fallback', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <TabErrorBoundary tabName="Test">
        <ThrowingComponent />
      </TabErrorBoundary>
    );

    const button = screen.getByRole('button');
    expect(button).toBeTruthy();

    consoleSpy.mockRestore();
  });
});
