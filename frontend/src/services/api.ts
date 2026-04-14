import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  Office,
  OfficeCreate,
  OfficeUpdate,
  Endpoint,
  EndpointCreate,
  EndpointUpdate,
  EndpointTestRequest,
  EndpointTestResponse,
  Report,
  ReportCreate,
  ReportStatusResponse,
  UploadUrlResponse,
} from '@/types';

const API_BASE_URL = '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const message = this.getErrorMessage(error);
        return Promise.reject(new Error(message));
      }
    );
  }

  private getErrorMessage(error: AxiosError): string {
    if (error.response) {
      const data = error.response.data as { detail?: string };
      return data.detail || `HTTP ${error.response.status}: ${error.response.statusText}`;
    }
    if (error.request) {
      return 'Network error: No response received from server';
    }
    return error.message || 'An unexpected error occurred';
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await axios.get('/health');
    return response.data;
  }

  // Office APIs
  async listOffices(skip = 0, limit = 100): Promise<Office[]> {
    const response = await this.client.get('/config/offices', {
      params: { skip, limit },
    });
    return response.data;
  }

  async getOffice(id: number): Promise<Office> {
    const response = await this.client.get(`/config/offices/${id}`);
    return response.data;
  }

  async createOffice(office: OfficeCreate): Promise<Office> {
    const response = await this.client.post('/config/offices', office);
    return response.data;
  }

  async updateOffice(id: number, office: OfficeUpdate): Promise<Office> {
    const response = await this.client.put(`/config/offices/${id}`, office);
    return response.data;
  }

  async deleteOffice(id: number): Promise<void> {
    await this.client.delete(`/config/offices/${id}`);
  }

  // Endpoint APIs
  async listEndpoints(officeId?: number, skip = 0, limit = 100): Promise<Endpoint[]> {
    const params: Record<string, unknown> = { skip, limit };
    if (officeId) params.office_id = officeId;
    const response = await this.client.get('/config/endpoints', { params });
    return response.data;
  }

  async getEndpoint(id: number): Promise<Endpoint> {
    const response = await this.client.get(`/config/endpoints/${id}`);
    return response.data;
  }

  async createEndpoint(endpoint: EndpointCreate): Promise<Endpoint> {
    const response = await this.client.post('/config/endpoints', endpoint);
    return response.data;
  }

  async updateEndpoint(id: number, endpoint: EndpointUpdate): Promise<Endpoint> {
    const response = await this.client.put(`/config/endpoints/${id}`, endpoint);
    return response.data;
  }

  async deleteEndpoint(id: number): Promise<void> {
    await this.client.delete(`/config/endpoints/${id}`);
  }

  async testEndpoint(id: number, testData?: EndpointTestRequest): Promise<EndpointTestResponse> {
    const response = await this.client.post(`/config/endpoints/${id}/test`, testData || {});
    return response.data;
  }

  // Report APIs
  async listReports(officeId?: number, status?: string, skip = 0, limit = 100): Promise<Report[]> {
    const params: Record<string, unknown> = { skip, limit };
    if (officeId) params.office_id = officeId;
    if (status) params.status = status;
    const response = await this.client.get('/reports', { params });
    return response.data;
  }

  async getReport(id: number): Promise<Report> {
    const response = await this.client.get(`/reports/${id}`);
    return response.data;
  }

  async createReport(report: ReportCreate): Promise<UploadUrlResponse> {
    const response = await this.client.post('/reports', report);
    return response.data;
  }

  async uploadFile(
    reportId: number,
    type: 'image' | 'video' | 'audio',
    file: File,
    index = 0,
    onProgress?: (progress: number) => void
  ): Promise<{ success: boolean; filename: string; path: string; size: number }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post(
      `/reports/${reportId}/upload?type=${type}&index=${index}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      }
    );
    return response.data;
  }

  async submitReport(id: number): Promise<{ success: boolean; report_id: number; status: string }> {
    const response = await this.client.post(`/reports/${id}/submit`);
    return response.data;
  }

  async getReportStatus(id: number): Promise<ReportStatusResponse> {
    const response = await this.client.get(`/reports/${id}/status`);
    return response.data;
  }

  async deleteReport(id: number): Promise<void> {
    await this.client.delete(`/reports/${id}`);
  }
}

export const api = new ApiClient();
