import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  RatingStars,
  RatingCard,
  SentimentTrend,
  EmployeeTrend,
  SentimentBadge,
  GapCorrelationCard,
} from '@/components/research-results/shared/InsideIntelHelpers';
import { GapCorrelation } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

// ---------------------------------------------------------------------------
// RatingStars
// ---------------------------------------------------------------------------
describe('RatingStars', () => {
  it('renders 5 star characters total', () => {
    const { container } = render(<RatingStars rating={3.5} />);
    const stars = container.querySelectorAll('span');
    expect(stars.length).toBe(5);
  });

  it('renders 5 filled stars for rating 5', () => {
    const { container } = render(<RatingStars rating={5} />);
    const yellowStars = Array.from(container.querySelectorAll('span')).filter(
      (s) => s.className.includes('yellow')
    );
    expect(yellowStars.length).toBe(5);
  });

  it('renders no filled stars for rating 0', () => {
    const { container } = render(<RatingStars rating={0} />);
    const yellowStars = Array.from(container.querySelectorAll('span')).filter(
      (s) => s.className.includes('yellow')
    );
    expect(yellowStars.length).toBe(0);
  });

  it('renders without crash when rating is undefined', () => {
    const { container } = render(<RatingStars rating={undefined as unknown as number} />);
    expect(container).toBeTruthy();
  });

  it('renders without crash when rating is null', () => {
    const { container } = render(<RatingStars rating={null as unknown as number} />);
    expect(container).toBeTruthy();
  });

  it('renders 0 stars when rating is 0', () => {
    const { container } = render(<RatingStars rating={0} />);
    const yellowStars = Array.from(container.querySelectorAll('span')).filter(
      (s) => s.className.includes('yellow')
    );
    expect(yellowStars.length).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// RatingCard
// ---------------------------------------------------------------------------
describe('RatingCard', () => {
  it('renders label and formatted value', () => {
    render(<RatingCard label="Work-Life Balance" value={3.8} />);
    expect(screen.getByText('Work-Life Balance')).toBeTruthy();
    expect(screen.getByText('3.8')).toBeTruthy();
  });

  it('applies green color class for high values', () => {
    render(<RatingCard label="Culture" value={4.2} />);
    const valueEl = screen.getByText('4.2');
    expect(valueEl.className).toContain('green');
  });

  it('applies red color class for low values', () => {
    render(<RatingCard label="Management" value={2.1} />);
    const valueEl = screen.getByText('2.1');
    expect(valueEl.className).toContain('red');
  });

  it('renders 0.0 when value is undefined', () => {
    render(<RatingCard label="Test" value={undefined as unknown as number} />);
    expect(screen.getByText('0.0')).toBeTruthy();
  });

  it('renders 0.0 when value is null', () => {
    render(<RatingCard label="Test" value={null as unknown as number} />);
    expect(screen.getByText('0.0')).toBeTruthy();
  });

  it('renders 0.0 when value is NaN', () => {
    render(<RatingCard label="Test" value={NaN} />);
    expect(screen.getByText('0.0')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// SentimentTrend
// ---------------------------------------------------------------------------
describe('SentimentTrend', () => {
  it('renders "Improving" label for improving trend', () => {
    render(<SentimentTrend trend="improving" />);
    expect(screen.getByText(/Improving/)).toBeTruthy();
  });

  it('renders "Declining" label for declining trend', () => {
    render(<SentimentTrend trend="declining" />);
    expect(screen.getByText(/Declining/)).toBeTruthy();
  });

  it('renders "Stable" label for stable trend', () => {
    render(<SentimentTrend trend="stable" />);
    expect(screen.getByText(/Stable/)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// EmployeeTrend
// ---------------------------------------------------------------------------
describe('EmployeeTrend', () => {
  it('renders growing trend', () => {
    render(<EmployeeTrend trend="growing" />);
    expect(screen.getByText(/Growing/)).toBeTruthy();
  });

  it('renders shrinking trend', () => {
    render(<EmployeeTrend trend="shrinking" />);
    expect(screen.getByText(/Shrinking/)).toBeTruthy();
  });

  it('renders stable trend', () => {
    render(<EmployeeTrend trend="stable" />);
    expect(screen.getByText(/Stable/)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// SentimentBadge
// ---------------------------------------------------------------------------
describe('SentimentBadge', () => {
  it('renders sentiment text capitalised', () => {
    render(<SentimentBadge sentiment="positive" />);
    expect(screen.getByText('positive')).toBeTruthy();
  });

  it('applies green background for positive', () => {
    render(<SentimentBadge sentiment="positive" />);
    const badge = screen.getByText('positive');
    expect(badge.className).toContain('green');
  });

  it('applies red background for negative', () => {
    render(<SentimentBadge sentiment="negative" />);
    const badge = screen.getByText('negative');
    expect(badge.className).toContain('red');
  });

  it('applies yellow background for mixed', () => {
    render(<SentimentBadge sentiment="mixed" />);
    const badge = screen.getByText('mixed');
    expect(badge.className).toContain('yellow');
  });

  it('accepts extra className', () => {
    render(<SentimentBadge sentiment="neutral" className="ml-2" />);
    const badge = screen.getByText('neutral');
    expect(badge.className).toContain('ml-2');
  });
});

// ---------------------------------------------------------------------------
// GapCorrelationCard
// ---------------------------------------------------------------------------
const techCorrelation: GapCorrelation = {
  gap_type: 'technology',
  description: 'No SIEM deployed',
  evidence: 'SOC analyst job posting requires "build SIEM from scratch"',
  evidence_type: 'supporting',
  confidence: 0.85,
  sales_implication: 'Strong opening for Microsoft Sentinel pitch',
};

describe('GapCorrelationCard', () => {
  it('renders gap type label', () => {
    render(<GapCorrelationCard correlation={techCorrelation} />);
    expect(screen.getByText(/technology gap/i)).toBeTruthy();
  });

  it('renders description', () => {
    render(<GapCorrelationCard correlation={techCorrelation} />);
    expect(screen.getByText('No SIEM deployed')).toBeTruthy();
  });

  it('renders evidence text', () => {
    render(<GapCorrelationCard correlation={techCorrelation} />);
    expect(screen.getByText(/SOC analyst job posting/)).toBeTruthy();
  });

  it('renders evidence type badge', () => {
    render(<GapCorrelationCard correlation={techCorrelation} />);
    expect(screen.getByText('supporting')).toBeTruthy();
  });

  it('renders confidence percentage', () => {
    render(<GapCorrelationCard correlation={techCorrelation} />);
    expect(screen.getByText('85%')).toBeTruthy();
  });

  it('renders sales implication', () => {
    render(<GapCorrelationCard correlation={techCorrelation} />);
    expect(screen.getByText(/Strong opening for Microsoft Sentinel pitch/)).toBeTruthy();
  });

  it('renders without crashing when sources omitted', () => {
    const { container } = render(<GapCorrelationCard correlation={techCorrelation} />);
    expect(container).toBeTruthy();
  });
});
