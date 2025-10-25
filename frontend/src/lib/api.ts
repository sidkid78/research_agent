import { 
  ResearchRequest, 
  JobSubmitResponse, 
  JobStatusResponse, 
  ResearchResult,
  BatchResearchRequest,
  BatchResearchResult,
  LiveResearchStartRequest,
  LiveResearchSession,
  LiveResearchSummary,
  ResearchAnalytics,
  ResearchHistoryItem,
  ResearchSearchFilters,
  UserResearchPreferences
} from './types';

// Enhanced API client for Academic Research Agent
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    let errorCode = 'UNKNOWN_ERROR';
    let errorDetails = undefined;
    
    try {
      const errorBody = await response.json();
      errorMessage = errorBody.detail || errorBody.message || errorMessage;
      errorCode = errorBody.code || errorCode;
      errorDetails = errorBody.details;
    } catch {
      // Could not parse error body, use default message
    }
    
    throw new ApiError(errorMessage, response.status, errorCode, errorDetails);
  }
  return response.json() as Promise<T>;
}

// Core Research API
export async function submitResearchJob(requestData: ResearchRequest): Promise<JobSubmitResponse> {
  const response = await fetch(`${API_BASE_URL}/research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestData),
  });
  return handleApiResponse<JobSubmitResponse>(response);
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/research/${jobId}/status`);
  return handleApiResponse<JobStatusResponse>(response);
}

export async function getJobDetails(jobId: string): Promise<ResearchRequest> {
  const response = await fetch(`${API_BASE_URL}/research/${jobId}/details`);
  return handleApiResponse<ResearchRequest>(response);
}

export async function getJobResult(jobId: string): Promise<ResearchResult> {
  const response = await fetch(`${API_BASE_URL}/research/${jobId}/result`);
  return handleApiResponse<ResearchResult>(response);
}

export async function cancelJob(jobId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/research/${jobId}/cancel`, {
    method: 'POST',
  });
  return handleApiResponse<{ success: boolean; message: string }>(response);
}

// Enhanced Academic Research API
export async function submitAcademicResearch(requestData: ResearchRequest): Promise<JobSubmitResponse> {
  const response = await fetch(`${API_BASE_URL}/academic-research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestData),
  });
  return handleApiResponse<JobSubmitResponse>(response);
}

export async function validatePubMedAccess(email: string): Promise<{ valid: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/academic-research/validate-pubmed`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });
  return handleApiResponse<{ valid: boolean; message: string }>(response);
}

export async function getAcademicSourcesPreview(topic: string): Promise<{
  arxiv_preview: Array<{ title: string; authors: string[]; abstract: string }>;
  pubmed_preview: Array<{ title: string; journal: string; abstract: string }>;
  estimated_sources: number;
}> {
  const response = await fetch(`${API_BASE_URL}/academic-research/preview?topic=${encodeURIComponent(topic)}`);
  return handleApiResponse(response);
}

// Batch Research API
export async function submitBatchResearch(requestData: BatchResearchRequest): Promise<{ batch_id: string; status: string }> {
  const response = await fetch(`${API_BASE_URL}/batch-research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestData),
  });
  return handleApiResponse(response);
}

export async function getBatchResearchStatus(batchId: string): Promise<{
  batch_id: string;
  status: string;
  progress: number;
  completed_topics: string[];
  failed_topics: string[];
}> {
  const response = await fetch(`${API_BASE_URL}/batch-research/${batchId}/status`);
  return handleApiResponse(response);
}

export async function getBatchResearchResults(batchId: string): Promise<BatchResearchResult> {
  const response = await fetch(`${API_BASE_URL}/batch-research/${batchId}/results`);
  return handleApiResponse<BatchResearchResult>(response);
}

// Live Research Session API
export async function startLiveResearchSession(requestData: LiveResearchStartRequest): Promise<LiveResearchSession> {
  const response = await fetch(`${API_BASE_URL}/live-research/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestData),
  });
  return handleApiResponse<LiveResearchSession>(response);
}

export async function getLiveResearchStatus(sessionId: string): Promise<LiveResearchSummary> {
  const response = await fetch(`${API_BASE_URL}/live-research/${sessionId}/status`);
  return handleApiResponse<LiveResearchSummary>(response);
}

export async function endLiveResearchSession(sessionId: string): Promise<LiveResearchSummary> {
  const response = await fetch(`${API_BASE_URL}/live-research/${sessionId}/end`, {
    method: 'POST',
  });
  return handleApiResponse<LiveResearchSummary>(response);
}

// WebSocket connection for live research
export function createLiveResearchWebSocket(
  sessionId: string,
  onMessage: (data: unknown) => void,
  onError: (error: Event) => void,
  onClose: () => void
): WebSocket {
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/live-research/${sessionId}/ws`;
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
      onError(new Event('parse_error'));
    }
  };
  
  ws.onerror = onError;
  ws.onclose = onClose;
  
  return ws;
}

// Research History and Analytics API
export async function getResearchHistory(
  filters?: ResearchSearchFilters,
  page: number = 1,
  limit: number = 20
): Promise<{
  items: ResearchHistoryItem[];
  total: number;
  page: number;
  pages: number;
}> {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    ...Object.fromEntries(
      Object.entries(filters || {}).map(([key, value]) => [
        key,
        typeof value === 'object' ? JSON.stringify(value) : String(value)
      ])
    )
  });
  
  const response = await fetch(`${API_BASE_URL}/research/history?${params}`);
  return handleApiResponse(response);
}

export async function getResearchAnalytics(dateRange?: { start: string; end: string }): Promise<ResearchAnalytics> {
  const params = dateRange ? new URLSearchParams({
    start_date: dateRange.start,
    end_date: dateRange.end
  }) : '';
  
  const response = await fetch(`${API_BASE_URL}/research/analytics?${params}`);
  return handleApiResponse<ResearchAnalytics>(response);
}

export async function deleteResearchJob(jobId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/research/${jobId}`, {
    method: 'DELETE',
  });
  return handleApiResponse(response);
}

// User Preferences API
export async function getUserPreferences(): Promise<UserResearchPreferences> {
  const response = await fetch(`${API_BASE_URL}/user/preferences`);
  return handleApiResponse<UserResearchPreferences>(response);
}

export async function updateUserPreferences(preferences: Partial<UserResearchPreferences>): Promise<UserResearchPreferences> {
  const response = await fetch(`${API_BASE_URL}/user/preferences`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(preferences),
  });
  return handleApiResponse<UserResearchPreferences>(response);
}

// File Export API
export async function exportResearchResult(
  jobId: string, 
  format: 'pdf' | 'docx' | 'md' | 'txt' = 'pdf'
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/research/${jobId}/export?format=${format}`);
  
  if (!response.ok) {
    throw new ApiError(`Export failed: ${response.statusText}`, response.status);
  }
  
  return response.blob();
}

export async function exportBatchResults(
  batchId: string,
  format: 'zip' | 'pdf' = 'zip'
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/batch-research/${batchId}/export?format=${format}`);
  
  if (!response.ok) {
    throw new ApiError(`Batch export failed: ${response.statusText}`, response.status);
  }
  
  return response.blob();
}

// Search and Discovery API
export async function searchResearchTopics(query: string): Promise<{
  suggestions: string[];
  related_topics: string[];
  trending_topics: string[];
}> {
  const response = await fetch(`${API_BASE_URL}/research/search-topics?q=${encodeURIComponent(query)}`);
  return handleApiResponse(response);
}

export async function getTrendingTopics(): Promise<{
  topics: Array<{
    topic: string;
    frequency: number;
    avg_confidence: number;
    sample_results: string[];
  }>;
}> {
  const response = await fetch(`${API_BASE_URL}/research/trending`);
  return handleApiResponse(response);
}

// Health Check API
export async function getApiHealth(): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: Record<string, 'up' | 'down'>;
  version: string;
  uptime_seconds: number;
}> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleApiResponse(response);
}

// Utility functions
export function downloadFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

// Export the ApiError class for use in components
export { ApiError };