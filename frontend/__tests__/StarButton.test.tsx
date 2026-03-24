import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StarButton from '@/components/projects/StarButton';

const mockListWorkProducts = vi.fn();
const mockDeleteWorkProduct = vi.fn();
const mockCreateWorkProduct = vi.fn();

vi.mock('@/lib/api', () => ({
  api: {
    listWorkProducts: (id: string) => mockListWorkProducts(id),
    deleteWorkProduct: (projectId: string, wpId: string) => mockDeleteWorkProduct(projectId, wpId),
    createWorkProduct: (projectId: string, data: object) => mockCreateWorkProduct(projectId, data),
  },
}));

const defaultProps = {
  projectId: 'p1',
  contentType: 'researchreport',
  objectId: 'obj1',
  category: 'insight' as const,
};

describe('StarButton', () => {
  beforeEach(() => {
    mockListWorkProducts.mockResolvedValue([]);
    mockDeleteWorkProduct.mockResolvedValue({});
    mockCreateWorkProduct.mockResolvedValue({});
  });

  it('renders a button', () => {
    render(<StarButton {...defaultProps} />);
    expect(screen.getByRole('button')).toBeTruthy();
  });

  it('shows "Save to work products" title when not starred', () => {
    render(<StarButton {...defaultProps} isStarred={false} />);
    expect(screen.getByTitle('Save to work products')).toBeTruthy();
  });

  it('shows "Remove from saved items" title when starred', () => {
    render(<StarButton {...defaultProps} isStarred={true} />);
    expect(screen.getByTitle('Remove from saved items')).toBeTruthy();
  });

  it('calls createWorkProduct when unstarred button is clicked', async () => {
    render(<StarButton {...defaultProps} isStarred={false} />);
    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => {
      expect(mockCreateWorkProduct).toHaveBeenCalledWith('p1', expect.objectContaining({
        object_id: 'obj1',
        category: 'insight',
      }));
    });
  });

  it('calls listWorkProducts then deleteWorkProduct when starred button is clicked', async () => {
    mockListWorkProducts.mockResolvedValue([
      { id: 'wp1', object_id: 'obj1', content_type_name: 'researchreport' },
    ]);
    render(<StarButton {...defaultProps} isStarred={true} />);
    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => {
      expect(mockListWorkProducts).toHaveBeenCalledWith('p1');
      expect(mockDeleteWorkProduct).toHaveBeenCalledWith('p1', 'wp1');
    });
  });

  it('calls onToggle(true) after starring', async () => {
    const onToggle = vi.fn();
    render(<StarButton {...defaultProps} isStarred={false} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => {
      expect(onToggle).toHaveBeenCalledWith(true);
    });
  });

  it('calls onToggle(false) after unstarring', async () => {
    mockListWorkProducts.mockResolvedValue([
      { id: 'wp1', object_id: 'obj1', content_type_name: 'researchreport' },
    ]);
    const onToggle = vi.fn();
    render(<StarButton {...defaultProps} isStarred={true} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => {
      expect(onToggle).toHaveBeenCalledWith(false);
    });
  });

  it('stops click event propagation', () => {
    const parentClick = vi.fn();
    render(
      <div onClick={parentClick}>
        <StarButton {...defaultProps} />
      </div>
    );
    fireEvent.click(screen.getByRole('button'));
    expect(parentClick).not.toHaveBeenCalled();
  });
});
