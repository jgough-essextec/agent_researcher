import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import RawTab from '@/components/research-results/tabs/RawTab';

vi.mock('@/lib/api', () => ({ api: {} }));

describe('RawTab', () => {
  // --- 1. Renders raw text content ---
  it('renders the result string verbatim', () => {
    render(<RawTab result="Raw research output goes here." />);
    expect(screen.getByText('Raw research output goes here.')).toBeTruthy();
  });

  // --- 2. Renders JSON string ---
  it('renders JSON string content without crashing', () => {
    const json = JSON.stringify({ company: 'Acme', revenue: '$1B' }, null, 2);
    render(<RawTab result={json} />);
    expect(screen.getByText(/"company"/)).toBeTruthy();
  });

  // --- 3. Renders multiline content ---
  it('renders multiline content in a pre element', () => {
    const multiline = 'Line 1\nLine 2\nLine 3';
    render(<RawTab result={multiline} />);
    const pre = document.querySelector('pre');
    expect(pre).toBeTruthy();
    expect(pre!.textContent).toContain('Line 1');
    expect(pre!.textContent).toContain('Line 2');
    expect(pre!.textContent).toContain('Line 3');
  });

  // --- 4. Empty string ---
  it('renders without crashing for empty result string', () => {
    const { container } = render(<RawTab result="" />);
    expect(container).toBeTruthy();
    const pre = document.querySelector('pre');
    expect(pre).toBeTruthy();
    expect(pre!.textContent).toBe('');
  });

  // --- 5. Uses pre element (not a div) ---
  it('wraps content in a pre element for whitespace preservation', () => {
    render(<RawTab result="  indented content  " />);
    const pre = document.querySelector('pre');
    expect(pre).toBeTruthy();
  });

  // --- 6. Does not interpret markdown ---
  it('does not render markdown **bold** as HTML strong', () => {
    render(<RawTab result="**This should not be bold**" />);
    const strongs = document.querySelectorAll('strong');
    expect(strongs.length).toBe(0);
    expect(screen.getByText('**This should not be bold**')).toBeTruthy();
  });

  // --- 7. Long content renders without crash ---
  it('renders long content without crashing', () => {
    const longResult = 'x'.repeat(10000);
    const { container } = render(<RawTab result={longResult} />);
    expect(container).toBeTruthy();
  });
});
