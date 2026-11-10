// ============================================================
// UIP Platform — API Service Client
// Aligned with backend API v1
// ============================================================

import type {
  Case,
  CaseCreate,
  DocumentRecord,
  AnalysisStatus,
  AnalysisFindings,
  Decision,
  AuditTrail,
  HumanReview,
  HumanReviewCreate,
  ScientificValidation,
  SystemHealth,
  Client,
  ClientCreate,
  ClientUpdate,
  ClientHistory,
  ClientHistoryCreate,
  DatasetStats,
  DatasetSample,
} from '../types';

const BASE = '/api/v1';

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json() as Promise<T>;
}

// ---- Cases ----
export const api = {
  // Cases
  listCases: (): Promise<Case[]> => request('/cases'),
  getCase: (id: string): Promise<Case> => request(`/cases/${id}`),
  createCase: (data: CaseCreate): Promise<Case> =>
    request('/cases', { method: 'POST', body: JSON.stringify(data) }),

  // Documents
  listDocuments: (caseId: string): Promise<DocumentRecord[]> =>
    request(`/cases/${caseId}/documents`),
  uploadDocument: (caseId: string, file: File): Promise<DocumentRecord> => {
    const form = new FormData();
    form.append('file', file);
    return request(`/cases/${caseId}/documents`, {
      method: 'POST',
      headers: {},          // let browser set multipart boundary
      body: form,
    });
  },

  // Analysis
  startAnalysis: (caseId: string): Promise<AnalysisFindings> =>
    request(`/cases/${caseId}/analyze`, { method: 'POST' }),
  getAnalysisStatus: (caseId: string): Promise<AnalysisStatus> =>
    request(`/cases/${caseId}/status`),
  getFindings: (caseId: string): Promise<AnalysisFindings> =>
    request(`/cases/${caseId}/findings`),
  getDecision: (caseId: string): Promise<Decision> =>
    request(`/cases/${caseId}/decision`),

  // Human Review
  submitReview: (caseId: string, data: HumanReviewCreate): Promise<HumanReview> =>
    request(`/cases/${caseId}/review`, { method: 'POST', body: JSON.stringify(data) }),
  getReviews: (caseId: string): Promise<HumanReview[]> =>
    request(`/cases/${caseId}/review`),

  // Audit
  getAuditTrail: (caseId: string): Promise<AuditTrail> =>
    request(`/cases/${caseId}/audit`),

  // Benchmarks
  getScientificValidation: (): Promise<ScientificValidation> =>
    request('/benchmarks/scientific-validation'),

  // System
  getHealth: (): Promise<SystemHealth> => request('/system/health'),

  // Clients
  listClients: (): Promise<Client[]> => request('/clients'),
  getClient: (id: string): Promise<Client> => request(`/clients/${id}`),
  createClient: (data: ClientCreate): Promise<Client> =>
    request('/clients', { method: 'POST', body: JSON.stringify(data) }),
  updateClient: (id: string, data: ClientUpdate): Promise<Client> =>
    request(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteClient: (id: string): Promise<{ message: string }> =>
    request(`/clients/${id}`, { method: 'DELETE' }),
  getClientCases: (id: string): Promise<Case[]> =>
    request(`/clients/${id}/cases`),
  getClientHistory: (id: string): Promise<ClientHistory[]> =>
    request(`/clients/${id}/history`),
  addClientHistory: (id: string, data: ClientHistoryCreate): Promise<ClientHistory> =>
    request(`/clients/${id}/history`, { method: 'POST', body: JSON.stringify(data) }),
  renewClientPolicy: (id: string): Promise<Case> =>
    request(`/clients/${id}/renew`, { method: 'POST' }),

  // Dataset
  getDatasetStats: (): Promise<DatasetStats> => request('/dataset/stats'),
  getDatasetSample: (n?: number): Promise<DatasetSample> => request(`/dataset/sample?n=${n || 10}`),
};
