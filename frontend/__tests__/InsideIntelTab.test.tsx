import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import InsideIntelTab from '@/components/research-results/tabs/InsideIntelTab';
import { InternalOpsIntel, WebSource } from '@/types';

vi.mock('@/lib/api', () => ({ api: {} }));

const sources: WebSource[] = [
  { uri: 'https://source1.com', title: 'Source One' },
];

const fullIntel: InternalOpsIntel = {
  id: 'i1',
  employee_sentiment: {
    overall_rating: 3.8,
    work_life_balance: 3.5,
    compensation: 3.9,
    culture: 4.0,
    management: 3.2,
    recommend_pct: 72,
    positive_themes: ['Good benefits', 'Flexible hours'],
    negative_themes: ['Slow promotion', 'Legacy tooling'],
    trend: 'improving',
  },
  linkedin_presence: {
    follower_count: 45000,
    engagement_level: 'medium',
    recent_posts: [
      { title: 'AI Partnership Announced', summary: 'We partnered with OpenAI.', date: '2026-01-10' },
    ],
    employee_trend: 'growing',
    notable_changes: ['Hired 50 engineers in Q1'],
  },
  social_media_mentions: [
    { platform: 'reddit', summary: 'Active discussion on r/sysadmin.', sentiment: 'neutral', topic: 'IT tooling' },
  ],
  job_postings: {
    total_openings: 120,
    departments_hiring: { Engineering: 60, Sales: 30, IT: 30 },
    skills_sought: ['Python', 'Kubernetes', 'Azure'],
    seniority_distribution: { Senior: 50, Mid: 40, Junior: 30 },
    urgency_signals: ['Multiple roles listed simultaneously'],
    insights: 'Heavy engineering hiring signals product investment.',
  },
  news_sentiment: {
    overall_sentiment: 'positive',
    coverage_volume: 'medium',
    topics: ['AI adoption', 'Cloud migration'],
    headlines: [
      { title: 'Acme Wins Cloud Deal', source: 'TechCrunch', date: '2026-01-05', sentiment: 'positive' },
    ],
  },
  key_insights: ['They are actively investing in AI tooling based on hiring.'],
  gap_correlations: [
    {
      gap_type: 'technology',
      description: 'No SIEM deployed',
      evidence: 'Job postings for SOC analyst with "build from scratch" note',
      evidence_type: 'supporting',
      confidence: 0.8,
      sales_implication: 'High receptivity to SIEM solution pitch',
    },
  ],
  confidence_score: 0.78,
  data_freshness: 'last_30_days',
  analysis_notes: 'Data sourced from LinkedIn and Glassdoor.',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('InsideIntelTab', () => {
  // --- 1. Employee sentiment section ---
  it('renders employee sentiment section with overall rating', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Employee Sentiment Overview')).toBeTruthy();
    expect(screen.getByText('3.8/5.0')).toBeTruthy();
    expect(screen.getByText('Overall Rating')).toBeTruthy();
  });

  // --- 2. Recommend percentage ---
  it('renders recommend percentage', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('72%')).toBeTruthy();
    expect(screen.getByText('Would Recommend')).toBeTruthy();
  });

  // --- 3. Positive and negative themes ---
  it('renders positive and negative themes', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Good benefits')).toBeTruthy();
    expect(screen.getByText('Flexible hours')).toBeTruthy();
    expect(screen.getByText('Slow promotion')).toBeTruthy();
    expect(screen.getByText('Legacy tooling')).toBeTruthy();
  });

  // --- 4. Job postings section ---
  it('renders job postings section with total openings', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Talent & Hiring Intelligence')).toBeTruthy();
    expect(screen.getByText('120')).toBeTruthy();
    expect(screen.getByText('Total Open Positions')).toBeTruthy();
  });

  // --- 5. Skills sought ---
  it('renders skills sought tags', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Python')).toBeTruthy();
    expect(screen.getByText('Kubernetes')).toBeTruthy();
    expect(screen.getByText('Azure')).toBeTruthy();
  });

  // --- 6. Urgency signals ---
  it('renders urgency signals', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Urgency Signals')).toBeTruthy();
    expect(screen.getByText('Multiple roles listed simultaneously')).toBeTruthy();
  });

  // --- 7. LinkedIn presence ---
  it('renders LinkedIn presence section', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Digital & Social Presence')).toBeTruthy();
    expect(screen.getByText('45,000')).toBeTruthy();
    expect(screen.getByText('LinkedIn Followers')).toBeTruthy();
  });

  // --- 8. Recent posts ---
  it('renders recent LinkedIn posts', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('AI Partnership Announced')).toBeTruthy();
    expect(screen.getByText('We partnered with OpenAI.')).toBeTruthy();
  });

  // --- 9. Social media mentions ---
  it('renders social media mentions', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Social Media Mentions')).toBeTruthy();
    expect(screen.getByText('reddit')).toBeTruthy();
    expect(screen.getByText('Active discussion on r/sysadmin.')).toBeTruthy();
  });

  // --- 10. News sentiment ---
  it('renders news coverage section', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('News Coverage')).toBeTruthy();
    expect(screen.getByText('Acme Wins Cloud Deal')).toBeTruthy();
  });

  // --- 11. Gap correlations ---
  it('renders gap correlation insights', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Gap Correlation Insights')).toBeTruthy();
    expect(screen.getByText('No SIEM deployed')).toBeTruthy();
    expect(screen.getByText('High receptivity to SIEM solution pitch')).toBeTruthy();
  });

  // --- 12. Key insights ---
  it('renders key insights section', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Key Insights & Recommendations')).toBeTruthy();
    expect(screen.getByText('They are actively investing in AI tooling based on hiring.')).toBeTruthy();
  });

  // --- 13. Confidence score footer ---
  it('renders confidence score in footer', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('78%')).toBeTruthy();
  });

  // --- 14. Analysis notes ---
  it('renders analysis notes', () => {
    render(<InsideIntelTab intel={fullIntel} />);
    expect(screen.getByText('Data sourced from LinkedIn and Glassdoor.')).toBeTruthy();
  });

  // --- 15. No crash without sources prop ---
  it('renders without crash when sources are omitted', () => {
    const { container } = render(<InsideIntelTab intel={fullIntel} />);
    expect(container).toBeTruthy();
  });

  // --- 16. No crash with sources ---
  it('renders without crash when sources are provided', () => {
    const { container } = render(<InsideIntelTab intel={fullIntel} sources={sources} />);
    expect(container).toBeTruthy();
  });

  // --- 17. No crash when all nested sentiment/job/linkedin/news fields are null ---
  it('renders without crash when all nested sentiment/job/linkedin/news fields are null', () => {
    const nullIntel = {
      id: 'null-test',
      employee_sentiment: {
        overall_rating: null,
        work_life_balance: null,
        compensation: null,
        culture: null,
        management: null,
        recommend_pct: null,
        positive_themes: null,
        negative_themes: null,
        trend: null,
      },
      linkedin_presence: {
        follower_count: null,
        engagement_level: 'medium' as const,
        recent_posts: null,
        employee_trend: 'stable' as const,
        notable_changes: null,
      },
      social_media_mentions: [],
      job_postings: {
        total_openings: 0,
        departments_hiring: null,
        skills_sought: null,
        seniority_distribution: null,
        urgency_signals: null,
        insights: '',
      },
      news_sentiment: {
        overall_sentiment: 'neutral' as const,
        coverage_volume: 'low' as const,
        topics: null,
        headlines: null,
      },
      key_insights: [],
      gap_correlations: [],
      confidence_score: null,
      data_freshness: 'last_30_days',
      analysis_notes: '',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    } as any;

    // Should NOT throw any TypeError
    const { container } = render(<InsideIntelTab intel={nullIntel} />);
    expect(container).toBeTruthy();
    // Should show 0.0/5.0 (not crash), since overall_rating is null -> defaults to 0
    expect(screen.queryByText('0.0/5.0')).not.toBeNull();
  });
});
