// Decision maker from research report
export interface DecisionMaker {
  name: string;
  title: string;
  background: string;
  linkedin_url?: string;
}

// News item from research report
export interface NewsItem {
  title: string;
  summary: string;
  date: string;
  source: string;
  url?: string;
}

// Structured research report (AGE-10)
export interface ResearchReport {
  id: string;
  company_overview: string;
  founded_year?: number;
  headquarters: string;
  employee_count: string;
  annual_revenue: string;
  website: string;
  recent_news: NewsItem[];
  decision_makers: DecisionMaker[];
  pain_points: string[];
  opportunities: string[];
  digital_maturity: string;
  ai_footprint: string;
  ai_adoption_stage: string;
  strategic_goals: string[];
  key_initiatives: string[];
  talking_points: string[];
  created_at: string;
  updated_at: string;
}

// Competitor case study (AGE-12)
export interface CompetitorCaseStudy {
  id: string;
  competitor_name: string;
  vertical: string;
  case_study_title: string;
  summary: string;
  technologies_used: string[];
  outcomes: string[];
  source_url: string;
  relevance_score: number;
  created_at: string;
}

// Gap analysis (AGE-13)
export interface GapAnalysis {
  id: string;
  technology_gaps: string[];
  capability_gaps: string[];
  process_gaps: string[];
  recommendations: string[];
  priority_areas: string[];
  confidence_score: number;
  analysis_notes: string;
  created_at: string;
  updated_at: string;
}

// Main research job with nested data
export interface ResearchJob {
  id: string;
  client_name: string;
  sales_history: string;
  prompt: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result: string;
  error: string;
  vertical?: string;
  report?: ResearchReport;
  competitor_case_studies?: CompetitorCaseStudy[];
  gap_analysis?: GapAnalysis;
  created_at: string;
  updated_at: string;
}

export interface ResearchFormData {
  client_name: string;
  sales_history: string;
  prompt: string;
}

export interface PromptTemplate {
  id: number;
  name: string;
  content: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}
