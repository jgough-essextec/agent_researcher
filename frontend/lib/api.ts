import {
  ResearchJob,
  ResearchFormData,
  PromptTemplate,
  ProjectListItem,
  Project,
  ProjectCreateData,
  Iteration,
  IterationCreateData,
  WorkProduct,
  Annotation,
  TimelineData,
  IterationComparison,
} from '@/types';

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
  async listResearch(): Promise<ResearchJob[]> {
    return this.request<ResearchJob[]>('/api/research/jobs/');
  }

  async createResearch(data: ResearchFormData): Promise<ResearchJob> {
    const job = await this.request<ResearchJob>('/api/research/', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    // Fire off the execute call (runs synchronously on backend, ~1-5 min)
    // Don't await — the frontend will poll for status
    this.executeResearch(job.id).catch(console.error);

    return job;
  }

  async executeResearch(id: string): Promise<ResearchJob> {
    return this.request<ResearchJob>(`/api/research/${id}/execute/`, {
      method: 'POST',
    });
  }

  async getResearch(id: string): Promise<ResearchJob> {
    return this.request<ResearchJob>(`/api/research/${id}/`);
  }

  async downloadResearchPdf(id: string): Promise<void> {
    const url = `${this.baseUrl}/api/research/${id}/export/pdf/`;
    const response = await fetch(url);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || `Failed to download PDF: ${response.status}`);
    }

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'research_report.pdf';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"]+)"?/);
      if (match) {
        filename = match[1];
      }
    }

    // Convert response to blob and trigger download
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
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

  // Project endpoints
  async listProjects(): Promise<ProjectListItem[]> {
    return this.request<ProjectListItem[]>('/api/projects/');
  }

  async getProject(id: string): Promise<Project> {
    return this.request<Project>(`/api/projects/${id}/`);
  }

  async createProject(data: ProjectCreateData): Promise<Project> {
    return this.request<Project>('/api/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProject(id: string, data: Partial<ProjectCreateData>): Promise<Project> {
    return this.request<Project>(`/api/projects/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteProject(id: string): Promise<void> {
    await this.request(`/api/projects/${id}/`, {
      method: 'DELETE',
    });
  }

  // Iteration endpoints
  async listIterations(projectId: string): Promise<Iteration[]> {
    return this.request<Iteration[]>(`/api/projects/${projectId}/iterations/`);
  }

  async getIteration(projectId: string, sequence: number): Promise<Iteration> {
    return this.request<Iteration>(`/api/projects/${projectId}/iterations/${sequence}/`);
  }

  async createIteration(projectId: string, data: IterationCreateData): Promise<Iteration> {
    return this.request<Iteration>(`/api/projects/${projectId}/iterations/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async startIteration(projectId: string, sequence: number): Promise<{ iteration_id: string; research_job_id: string; status: string }> {
    return this.request(`/api/projects/${projectId}/iterations/${sequence}/start/`, {
      method: 'POST',
    });
  }

  async pollIteration(
    projectId: string,
    sequence: number,
    onUpdate: (iteration: Iteration) => void,
    intervalMs: number = 2000
  ): Promise<Iteration> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const iteration = await this.getIteration(projectId, sequence);
          onUpdate(iteration);

          if (iteration.status === 'completed' || iteration.status === 'failed') {
            resolve(iteration);
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

  // Timeline and comparison
  async getTimeline(projectId: string): Promise<TimelineData> {
    return this.request<TimelineData>(`/api/projects/${projectId}/timeline/`);
  }

  async compareIterations(projectId: string, seqA: number, seqB: number): Promise<IterationComparison> {
    return this.request<IterationComparison>(`/api/projects/${projectId}/compare/?a=${seqA}&b=${seqB}`);
  }

  // Work product endpoints
  async listWorkProducts(projectId: string): Promise<WorkProduct[]> {
    return this.request<WorkProduct[]>(`/api/projects/${projectId}/work-products/`);
  }

  async createWorkProduct(projectId: string, data: {
    content_type: string;
    object_id: string;
    category: string;
    source_iteration_id?: string;
    notes?: string;
  }): Promise<WorkProduct> {
    return this.request<WorkProduct>(`/api/projects/${projectId}/work-products/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateWorkProduct(projectId: string, id: string, data: Partial<WorkProduct>): Promise<WorkProduct> {
    return this.request<WorkProduct>(`/api/projects/${projectId}/work-products/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteWorkProduct(projectId: string, id: string): Promise<void> {
    await this.request(`/api/projects/${projectId}/work-products/${id}/`, {
      method: 'DELETE',
    });
  }

  // Annotation endpoints
  async listAnnotations(projectId: string): Promise<Annotation[]> {
    return this.request<Annotation[]>(`/api/projects/${projectId}/annotations/`);
  }

  async createAnnotation(projectId: string, data: {
    content_type: string;
    object_id: string;
    text: string;
  }): Promise<Annotation> {
    return this.request<Annotation>(`/api/projects/${projectId}/annotations/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAnnotation(projectId: string, id: string, data: { text: string }): Promise<Annotation> {
    return this.request<Annotation>(`/api/projects/${projectId}/annotations/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteAnnotation(projectId: string, id: string): Promise<void> {
    await this.request(`/api/projects/${projectId}/annotations/${id}/`, {
      method: 'DELETE',
    });
  }
}

export const api = new ApiClient(API_URL);
