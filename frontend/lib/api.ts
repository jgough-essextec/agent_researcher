import { ResearchJob, ResearchFormData, PromptTemplate } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  // Research endpoints
  async createResearch(data: ResearchFormData): Promise<ResearchJob> {
    return this.request<ResearchJob>('/api/research/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getResearch(id: string): Promise<ResearchJob> {
    return this.request<ResearchJob>(`/api/research/${id}/`);
  }

  async pollResearch(
    id: string,
    onUpdate: (job: ResearchJob) => void,
    intervalMs: number = 2000
  ): Promise<ResearchJob> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const job = await this.getResearch(id);
          onUpdate(job);

          if (job.status === 'completed' || job.status === 'failed') {
            resolve(job);
          } else {
            setTimeout(poll, intervalMs);
          }
        } catch (error) {
          reject(error);
        }
      };
      poll();
    });
  }

  // Prompt endpoints
  async getDefaultPrompt(): Promise<PromptTemplate> {
    return this.request<PromptTemplate>('/api/prompts/default/');
  }

  async updateDefaultPrompt(content: string): Promise<PromptTemplate> {
    return this.request<PromptTemplate>('/api/prompts/default/', {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }
}

export const api = new ApiClient(API_URL);
