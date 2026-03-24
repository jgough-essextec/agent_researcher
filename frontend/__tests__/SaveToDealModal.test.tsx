import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SaveToDealModal from '@/components/SaveToDealModal';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockListProjects = vi.fn();
const mockCreateProject = vi.fn();
const mockCreateWorkProduct = vi.fn();

vi.mock('@/lib/api', () => ({
  api: {
    listProjects: (...args: unknown[]) => mockListProjects(...args),
    createProject: (...args: unknown[]) => mockCreateProject(...args),
    createWorkProduct: (...args: unknown[]) => mockCreateWorkProduct(...args),
  },
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const baseProps = {
  clientName: 'Acme Corp',
  contentType: 'research.gapanalysis',
  objectId: 'obj-uuid-456',
  category: 'gap' as const,
  onClose: vi.fn(),
  onSaved: vi.fn(),
};

const mockProject = {
  id: 'proj-111',
  name: 'Acme Deal',
  client_name: 'Acme Corp',
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('SaveToDealModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: empty project list
    mockListProjects.mockResolvedValue([]);
  });

  describe('initial render', () => {
    it('renders "Save to Deal" heading', async () => {
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => {
        expect(screen.getByText('Save to Deal')).toBeInTheDocument();
      });
    });

    it('renders close button', async () => {
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
      });
    });

    it('calls listProjects on mount', async () => {
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => {
        expect(mockListProjects).toHaveBeenCalledTimes(1);
      });
    });

    it('defaults to "New Deal" tab when no projects exist', async () => {
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/acme corp deal/i)).toBeInTheDocument();
      });
    });

    it('shows both tabs when projects exist', async () => {
      mockListProjects.mockResolvedValue([mockProject]);

      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Existing Deal' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'New Deal' })).toBeInTheDocument();
      });
    });

    it('defaults to "Existing Deal" tab when projects are present', async () => {
      mockListProjects.mockResolvedValue([mockProject]);

      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => {
        // The select element renders in the existing-deal tab (no label htmlFor, query by role)
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });
    });
  });

  describe('close behaviour', () => {
    it('calls onClose when close button is clicked', async () => {
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByRole('button', { name: /close/i }));
      fireEvent.click(screen.getByRole('button', { name: /close/i }));

      expect(baseProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when Cancel button is clicked', async () => {
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByRole('button', { name: /cancel/i }));
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      expect(baseProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('saving to a new deal', () => {
    it('shows validation error when deal name is empty', async () => {
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByRole('button', { name: /save/i }));
      // Click Save without entering a name
      fireEvent.click(screen.getByRole('button', { name: 'Save' }));

      await waitFor(() => {
        expect(screen.getByText(/enter a deal name/i)).toBeInTheDocument();
      });
    });

    it('creates project then work product when new deal name is entered', async () => {
      const newProject = { id: 'proj-new', name: 'New Deal', client_name: 'Acme Corp' };
      mockCreateProject.mockResolvedValue(newProject);
      mockCreateWorkProduct.mockResolvedValue({ id: 'wp-1' });

      const user = userEvent.setup();
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByPlaceholderText(/acme corp deal/i));

      await user.type(screen.getByPlaceholderText(/acme corp deal/i), 'New Deal');
      await user.click(screen.getByRole('button', { name: 'Save' }));

      await waitFor(() => {
        expect(mockCreateProject).toHaveBeenCalledWith({
          name: 'New Deal',
          client_name: 'Acme Corp',
        });
        expect(mockCreateWorkProduct).toHaveBeenCalledWith('proj-new', {
          content_type: baseProps.contentType,
          object_id: baseProps.objectId,
          category: baseProps.category,
        });
      });
    });

    it('calls onSaved and onClose after successful save', async () => {
      const newProject = { id: 'proj-new', name: 'New Deal', client_name: 'Acme Corp' };
      mockCreateProject.mockResolvedValue(newProject);
      mockCreateWorkProduct.mockResolvedValue({ id: 'wp-1' });

      const user = userEvent.setup();
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByPlaceholderText(/acme corp deal/i));

      await user.type(screen.getByPlaceholderText(/acme corp deal/i), 'New Deal');
      await user.click(screen.getByRole('button', { name: 'Save' }));

      await waitFor(() => {
        expect(baseProps.onSaved).toHaveBeenCalledTimes(1);
        expect(baseProps.onClose).toHaveBeenCalledTimes(1);
      });
    });

    it('shows error message when API call fails', async () => {
      mockCreateProject.mockRejectedValue(new Error('Network error'));

      const user = userEvent.setup();
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByPlaceholderText(/acme corp deal/i));

      await user.type(screen.getByPlaceholderText(/acme corp deal/i), 'Failing Deal');
      await user.click(screen.getByRole('button', { name: 'Save' }));

      await waitFor(() => {
        expect(screen.getByText(/failed to save/i)).toBeInTheDocument();
      });
    });
  });

  describe('saving to an existing deal', () => {
    it('creates work product when existing deal is selected and saved', async () => {
      mockListProjects.mockResolvedValue([mockProject]);
      mockCreateWorkProduct.mockResolvedValue({ id: 'wp-2' });

      const user = userEvent.setup();
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByRole('combobox'));

      await user.selectOptions(screen.getByRole('combobox'), 'proj-111');
      await user.click(screen.getByRole('button', { name: 'Save' }));

      await waitFor(() => {
        expect(mockCreateProject).not.toHaveBeenCalled();
        expect(mockCreateWorkProduct).toHaveBeenCalledWith('proj-111', {
          content_type: baseProps.contentType,
          object_id: baseProps.objectId,
          category: baseProps.category,
        });
      });
    });

    it('shows error when no project is selected', async () => {
      mockListProjects.mockResolvedValue([mockProject]);

      const user = userEvent.setup();
      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByRole('button', { name: 'Save' }));
      await user.click(screen.getByRole('button', { name: 'Save' }));

      await waitFor(() => {
        expect(screen.getByText(/select a deal/i)).toBeInTheDocument();
      });
    });
  });

  describe('tab switching', () => {
    it('switches to New Deal tab when clicked', async () => {
      mockListProjects.mockResolvedValue([mockProject]);
      const user = userEvent.setup();

      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByRole('button', { name: 'New Deal' }));
      await user.click(screen.getByRole('button', { name: 'New Deal' }));

      expect(screen.getByPlaceholderText(/acme corp deal/i)).toBeInTheDocument();
    });

    it('switches back to Existing Deal tab when clicked', async () => {
      mockListProjects.mockResolvedValue([mockProject]);
      const user = userEvent.setup();

      render(<SaveToDealModal {...baseProps} />);

      await waitFor(() => screen.getByRole('button', { name: 'New Deal' }));
      await user.click(screen.getByRole('button', { name: 'New Deal' }));
      await user.click(screen.getByRole('button', { name: 'Existing Deal' }));

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });
    });
  });
});
