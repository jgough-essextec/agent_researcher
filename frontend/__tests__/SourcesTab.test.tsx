import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import SourcesTab from '@/components/research-results/tabs/SourcesTab';
import { WebSource } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const sources: WebSource[] = [
  { uri: 'https://techcrunch.com/article-1', title: 'TechCrunch: AI Adoption Surge' },
  { uri: 'https://bloomberg.com/article-2', title: 'Bloomberg: Cloud Market Update' },
  { uri: 'https://reuters.com/article-3', title: 'Reuters: Supply Chain News' },
];

describe('SourcesTab', () => {
  // --- 1. Count message ---
  it('renders correct source count for multiple sources', () => {
    render(<SourcesTab sources={sources} />);
    expect(screen.getByText(/Research grounded with 3 web sources/)).toBeTruthy();
  });

  it('renders singular "source" for single item', () => {
    render(<SourcesTab sources={[sources[0]]} />);
    expect(screen.getByText(/Research grounded with 1 web source/)).toBeTruthy();
    expect(screen.queryByText(/1 web sources/)).toBeNull();
  });

  it('renders zero count message for empty array', () => {
    render(<SourcesTab sources={[]} />);
    expect(screen.getByText(/Research grounded with 0 web source/)).toBeTruthy();
  });

  // --- 2. Source titles ---
  it('renders all source titles', () => {
    render(<SourcesTab sources={sources} />);
    expect(screen.getByText('TechCrunch: AI Adoption Surge')).toBeTruthy();
    expect(screen.getByText('Bloomberg: Cloud Market Update')).toBeTruthy();
    expect(screen.getByText('Reuters: Supply Chain News')).toBeTruthy();
  });

  it('shows "Untitled Source" when title is empty', () => {
    render(<SourcesTab sources={[{ uri: 'https://example.com', title: '' }]} />);
    expect(screen.getByText('Untitled Source')).toBeTruthy();
  });

  // --- 3. Source URIs as links ---
  it('renders source URIs as anchor links', () => {
    render(<SourcesTab sources={sources} />);
    const links = document.querySelectorAll('a[href="https://techcrunch.com/article-1"]');
    expect(links.length).toBeGreaterThan(0);
  });

  it('all source links open in new tab', () => {
    render(<SourcesTab sources={sources} />);
    const links = document.querySelectorAll('a[target="_blank"]');
    expect(links.length).toBeGreaterThan(0);
  });

  // --- 4. Numbered badges ---
  it('renders numbered badges for each source', () => {
    render(<SourcesTab sources={sources} />);
    expect(screen.getByText('1')).toBeTruthy();
    expect(screen.getByText('2')).toBeTruthy();
    expect(screen.getByText('3')).toBeTruthy();
  });

  // --- 5. Source IDs for anchor linking ---
  it('renders id="source-N" anchors for citation links', () => {
    render(<SourcesTab sources={sources} />);
    expect(document.getElementById('source-1')).toBeTruthy();
    expect(document.getElementById('source-2')).toBeTruthy();
    expect(document.getElementById('source-3')).toBeTruthy();
  });

  // --- 6. Open buttons ---
  it('renders Open link buttons for sources with URIs', () => {
    render(<SourcesTab sources={sources} />);
    const openLinks = screen.getAllByText('Open');
    expect(openLinks.length).toBe(3);
  });

  // --- 7. Footer note ---
  it('renders the Google Search grounding footnote', () => {
    render(<SourcesTab sources={sources} />);
    expect(screen.getByText(/Google Search grounding/)).toBeTruthy();
  });

  // --- 8. No crash with empty sources ---
  it('renders without crashing with empty sources array', () => {
    const { container } = render(<SourcesTab sources={[]} />);
    expect(container).toBeTruthy();
  });
});
