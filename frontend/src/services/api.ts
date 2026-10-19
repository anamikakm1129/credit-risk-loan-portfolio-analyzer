const API_BASE = '/api/v1';

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error ${res.status}: ${errorText || res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: (reportingDate?: string) =>
    fetchJson<any>(`/dashboard/summary${reportingDate ? `?reporting_date=${reportingDate}` : ''}`),
  
  getDashboardTrends: (reportingDate?: string) =>
    fetchJson<any>(`/dashboard/trends${reportingDate ? `?reporting_date=${reportingDate}` : ''}`),

  // Borrowers
  getBorrowers: (params: Record<string, any>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
    });
    return fetchJson<any>(`/borrowers?${query.toString()}`);
  },

  getBorrowerProfile: (borrowerId: string, reportingDate?: string) =>
    fetchJson<any>(`/borrowers/${borrowerId}${reportingDate ? `?reporting_date=${reportingDate}` : ''}`),

  // Loans
  getLoans: (params: Record<string, any>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
    });
    return fetchJson<any>(`/loans?${query.toString()}`);
  },

  getLoanDetail: (loanId: string, reportingDate?: string) =>
    fetchJson<any>(`/loans/${loanId}${reportingDate ? `?reporting_date=${reportingDate}` : ''}`),

  // Repayments
  getRepaymentsOverview: (reportingDate?: string) =>
    fetchJson<any>(`/repayments/overview${reportingDate ? `?reporting_date=${reportingDate}` : ''}`),

  getRepaymentTransactions: (params: Record<string, any>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
    });
    return fetchJson<any>(`/repayments/transactions?${query.toString()}`);
  },

  // Risk
  getRiskSegments: (reportingDate?: string) =>
    fetchJson<any>(`/risk/segments${reportingDate ? `?reporting_date=${reportingDate}` : ''}`),

  getRiskRules: () =>
    fetchJson<any>('/risk/rules'),

  simulateRisk: (payload: any) =>
    fetchJson<any>('/risk/simulate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Analytics
  getVintageAnalysis: (reportingDate?: string) =>
    fetchJson<any>(`/analysis/vintage${reportingDate ? `?reporting_date=${reportingDate}` : ''}`),

  getCreditScoreBands: (reportingDate?: string) =>
    fetchJson<any>(`/analysis/credit-score-bands${reportingDate ? `?reporting_date=${reportingDate}` : ''}`),

  // Reports
  generateReport: (payload: any) =>
    fetchJson<any>('/reports', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getReportsHistory: () =>
    fetchJson<any>('/reports/history'),

  // Data Quality
  getLatestDataQuality: () =>
    fetchJson<any>('/data-quality/latest'),

  runDataQualityDiagnostics: () =>
    fetchJson<any>('/data-quality/run-diagnostics', { method: 'POST' }),
};

