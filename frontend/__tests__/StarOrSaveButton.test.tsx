import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StarOrSaveButton from '@/components/research-results/shared/StarOrSaveButton';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockCreateWorkProduct = vi.fn();
const mockListProjects = vi.fn();
const mockCreateProject = vi.fn();
const mockListWorkProducts = vi.fn();
const mockDeleteWorkProduct = vi.fn();

vi.mock('@/lib/api', () => ({
  api: {
    createWorkProduct: (...args: unknown[]) => mockCreateWorkProduct(...args),
    listProjects: (...args: unknown[]) => mockListProjects(...args),
    createProject: (...args: unknown[]) => mockCreateProject(...args),
    listWorkProducts: (...args: unknown[]) => mockListWorkProducts(...args),
    deleteWorkProduct: (...args: unknown[]) => mockDeleteWorkProduct(...args),
  },
}));

// Stub StarButton to avoid deep API calls
vi.mock('@/components/projects/StarButton', () => ({
  default: ({ projectId }: { projectId: string }) => (
    <button data-testid="star-button" data-project-id={projectId}>
      StarButton
    </button>
  ),
}));

// Stub SaveToDealModal
vi.mock('@/components/SaveToDealModal', () => ({
  default: ({ onClose, onSaved, clientName }: { onClose: () => void; onSaved: () => void; clientName: string }) => (
    <div data-testid="save-modal">
      <span data-testid="modal-client">{clientName}</span>
      <button onClick={onSaved} data-testid="modal-save">Save</button>
      <button onClick={onClose} data-testid="modal-close">Close</button>
    </div>
  ),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const baseProps = {
  clientName: 'TestCo',
  contentType: 'research.researchreport',
  objectId: 'obj-uuid-123',
  category: 'insight' as const,
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('StarOrSaveButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('conditional rendering — with projectId', () => {
    it('renders StarButton when projectId is provided', () => {
      render(
        <StarOrSaveButton
          {...baseProps}
          projectId="proj-123"
          iterationId="iter-456"
        />
      );

      expect(screen.getByTestId('star-button')).toBeInTheDocument();
    });

    it('StarButton receives the correct projectId', () => {
      render(
        <StarOrSaveButton
          {...baseProps}
          projectId="proj-abc"
        />
      );

      expect(screen.getByTestId('star-button')).toHaveAttribute('data-project-id', 'proj-abc');
    });

    it('does not render the save-to-deal button when projectId is provided', () => {
      render(
        <StarOrSaveButton
          {...baseProps}
          projectId="proj-123"
        />
      );

      expect(screen.queryByTitle(/save to deal/i)).toBeNull();
    });

    it('does not render SaveToDealModal when projectId is provided', () => {
      render(
        <StarOrSaveButton
          {...baseProps}
          projectId="proj-123"
        />
      );

      expect(screen.queryByTestId('save-modal')).toBeNull();
    });
  });

  describe('conditional rendering — without projectId', () => {
    it('renders the save-to-deal star button when projectId is absent', () => {
      render(<StarOrSaveButton {...baseProps} />);

      expect(screen.getByTitle(/save to deal/i)).toBeInTheDocument();
    });

    it('does not render StarButton when projectId is absent', () => {
      render(<StarOrSaveButton {...baseProps} />);

      expect(screen.queryByTestId('star-button')).toBeNull();
    });

    it('does not render modal initially', () => {
      render(<StarOrSaveButton {...baseProps} />);

      expect(screen.queryByTestId('save-modal')).toBeNull();
    });
  });

  describe('save modal lifecycle', () => {
    it('opens SaveToDealModal when button is clicked', () => {
      render(<StarOrSaveButton {...baseProps} />);

      fireEvent.click(screen.getByTitle(/save to deal/i));

      expect(screen.getByTestId('save-modal')).toBeInTheDocument();
    });

    it('passes clientName to SaveToDealModal', () => {
      render(<StarOrSaveButton {...baseProps} clientName="Big Corp" />);

      fireEvent.click(screen.getByTitle(/save to deal/i));

      expect(screen.getByTestId('modal-client').textContent).toBe('Big Corp');
    });

    it('closes modal when onClose is called', () => {
      render(<StarOrSaveButton {...baseProps} />);

      fireEvent.click(screen.getByTitle(/save to deal/i));
      expect(screen.getByTestId('save-modal')).toBeInTheDocument();

      fireEvent.click(screen.getByTestId('modal-close'));

      expect(screen.queryByTestId('save-modal')).toBeNull();
    });

    it('marks button as saved when onSaved is called', async () => {
      render(<StarOrSaveButton {...baseProps} />);

      fireEvent.click(screen.getByTitle(/save to deal/i));
      fireEvent.click(screen.getByTestId('modal-save'));

      await waitFor(() => {
        expect(screen.getByTitle(/saved to deal/i)).toBeInTheDocument();
      });
    });

    it('closes modal when close is explicitly triggered after save', async () => {
      render(<StarOrSaveButton {...baseProps} />);

      fireEvent.click(screen.getByTitle(/save to deal/i));
      // Simulate saved callback then close callback (as real SaveToDealModal does)
      fireEvent.click(screen.getByTestId('modal-save'));    // triggers onSaved
      fireEvent.click(screen.getByTestId('modal-close'));   // triggers onClose

      await waitFor(() => {
        expect(screen.queryByTestId('save-modal')).toBeNull();
      });
    });

    it('button click stops event propagation', () => {
      const parentHandler = vi.fn();
      render(
        <div onClick={parentHandler}>
          <StarOrSaveButton {...baseProps} />
        </div>
      );

      fireEvent.click(screen.getByTitle(/save to deal/i));

      expect(parentHandler).not.toHaveBeenCalled();
    });
  });

  describe('saved state styling', () => {
    it('button shows yellow colour when saved', async () => {
      render(<StarOrSaveButton {...baseProps} />);

      fireEvent.click(screen.getByTitle(/save to deal/i));
      fireEvent.click(screen.getByTestId('modal-save'));

      await waitFor(() => {
        const btn = screen.getByTitle(/saved to deal/i);
        expect(btn.className).toContain('text-yellow-500');
      });
    });

    it('button shows gray colour when not yet saved', () => {
      render(<StarOrSaveButton {...baseProps} />);

      const btn = screen.getByTitle(/save to deal/i);
      expect(btn.className).toContain('text-gray-400');
    });
  });

  describe('size prop', () => {
    it('renders without error when size is "sm"', () => {
      render(<StarOrSaveButton {...baseProps} size="sm" />);
      expect(screen.getByTitle(/save to deal/i)).toBeInTheDocument();
    });

    it('renders without error when size is "lg"', () => {
      render(<StarOrSaveButton {...baseProps} size="lg" />);
      expect(screen.getByTitle(/save to deal/i)).toBeInTheDocument();
    });
  });
});
