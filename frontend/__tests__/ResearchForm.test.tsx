import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ResearchForm from '@/components/ResearchForm';

// Mock the api module
vi.mock('@/lib/api', () => ({
  api: {
    getDefaultPrompt: vi.fn().mockResolvedValue({
      id: 1,
      name: 'default',
      content: 'Test prompt template',
      is_default: true,
    }),
    createResearch: vi.fn().mockResolvedValue({
      id: '123',
      client_name: 'Test Corp',
      sales_history: '',
      status: 'pending',
      result: '',
      error: '',
    }),
    pollResearch: vi.fn().mockImplementation((id, onUpdate) => {
      onUpdate({
        id: '123',
        client_name: 'Test Corp',
        sales_history: '',
        status: 'completed',
        result: 'Research results',
        error: '',
      });
      return Promise.resolve({
        id: '123',
        client_name: 'Test Corp',
        sales_history: '',
        status: 'completed',
        result: 'Research results',
        error: '',
      });
    }),
  },
}));

describe('ResearchForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the form with required fields', async () => {
    render(<ResearchForm />);

    expect(screen.getByLabelText(/client name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/past sales history/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run research/i })).toBeInTheDocument();
  });

  it('shows validation error when client name is empty', async () => {
    render(<ResearchForm />);

    const submitButton = screen.getByRole('button', { name: /run research/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/client name is required/i)).toBeInTheDocument();
    });
  });

  it('allows entering client name and sales history', () => {
    render(<ResearchForm />);

    const clientNameInput = screen.getByLabelText(/client name/i);
    const salesHistoryInput = screen.getByLabelText(/past sales history/i);

    fireEvent.change(clientNameInput, { target: { value: 'Acme Corp' } });
    fireEvent.change(salesHistoryInput, { target: { value: 'Previous purchase: $50k' } });

    expect(clientNameInput).toHaveValue('Acme Corp');
    expect(salesHistoryInput).toHaveValue('Previous purchase: $50k');
  });

  it('shows prompt editor when expanded', async () => {
    render(<ResearchForm />);

    const expandButton = screen.getByRole('button', { name: /research prompt/i });
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/enter your research prompt/i)).toBeInTheDocument();
    });
  });
});
