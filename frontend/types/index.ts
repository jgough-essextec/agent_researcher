export interface ResearchJob {
  id: string;
  client_name: string;
  sales_history: string;
  prompt: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result: string;
  error: string;
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
