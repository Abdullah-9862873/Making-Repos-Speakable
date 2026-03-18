import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 300000,
    });
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        console.error('[API] Response error:', error);
        return Promise.reject(error);
      }
    );
  }

  async getHealth(): Promise<any> {
    const response = await this.client.get('/health');
    return response.data;
  }

  async getInfo(): Promise<any> {
    const response = await this.client.get('/');
    return response.data;
  }

  async validateRepo(repo: string): Promise<any> {
    const response = await this.client.post('/validate-repo', {
      repo,
    });
    return response.data;
  }

  async ingestCourse(repo?: string, extensions?: string[]): Promise<any> {
    const response = await this.client.post('/ingest', {
      repo,
      extensions,
    });
    return response.data;
  }

  async getIngestStatus(): Promise<any> {
    const response = await this.client.get('/ingest/status');
    return response.data;
  }

  async clearIngestion(): Promise<any> {
    const response = await this.client.post('/ingest/clear');
    return response.data;
  }

  async replaceIngestion(repo?: string, extensions?: string[]): Promise<any> {
    const response = await this.client.post('/ingest/replace', {
      repo,
      extensions,
    });
    return response.data;
  }

  async ingestSingleFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/ingest/single', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async askSingleFile(question: string, top_k: number = 5): Promise<any> {
    const formData = new FormData();
    formData.append('question', question);
    formData.append('top_k', top_k.toString());
    const response = await this.client.post('/ask/single', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async clearSingleFile(): Promise<any> {
    const response = await this.client.post('/ingest/single/clear');
    return response.data;
  }

  async askQuestion(params: {
    question: string;
    top_k?: number;
    threshold?: number;
    prompt_type?: string;
    include_voice?: boolean;
  }): Promise<any> {
    const response = await this.client.post('/ask', params);
    return response.data;
  }

  async ragQuery(query: string, top_k: number = 5, threshold: number = 0.7): Promise<any> {
    const response = await this.client.post('/rag/query', null, {
      params: { query, top_k, threshold },
    });
    return response.data;
  }

  async checkConnection(): Promise<boolean> {
    try {
      await this.getHealth();
      return true;
    } catch {
      return false;
    }
  }
}

export const apiService = new ApiService();

export interface AskRequest {
  question: string;
  top_k?: number;
  threshold?: number;
  prompt_type?: string;
  include_voice?: boolean;
}

export interface AskResponse {
  question: string;
  answer: string;
  has_context: boolean;
  context_used: boolean;
  sources: string[];
  num_contexts: number;
  top_score: number;
  has_code: boolean;
  code_blocks: CodeBlock[];
  voice_audio?: string;
}

export interface CodeBlock {
  language: string;
  code: string;
}

export interface IngestResponse {
  status: string;
  message: string;
  chunks_created: number;
  vectors_stored: number;
}

export interface HealthResponse {
  status: string;
  phase: string;
  version: string;
  components?: Record<string, string>;
}

export default apiService;
