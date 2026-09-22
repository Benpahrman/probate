/**
 * Gieni OS - Strongly Typed API Client Service
 * Interacts directly with Platform API (/api and /api/v1)
 */

import {
  OpportunitySummary,
  FullPOFDossier,
  QualityControlAuditSummary,
  ExceptionItem,
  CaseItem,
} from '../types';

const API_BASE = '/api/v1';

const DEFAULT_HEADERS: Record<string, string> = {
  'Content-Type': 'application/json',
  'x-clerk-user-id': 'user_internal_operator',
  'x-clerk-role': 'Platform Admin',
};

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status} ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const ApiService = {
  // Opportunities
  async getOpportunities(params?: {
    stage?: string;
    county_id?: string;
    authority_status?: string;
  }): Promise<OpportunitySummary[]> {
    const query = new URLSearchParams();
    if (params?.stage) query.append('workflow_stage', params.stage);
    if (params?.county_id) query.append('county_id', params.county_id);
    if (params?.authority_status) query.append('authority_status', params.authority_status);

    const url = `${API_BASE}/opportunities${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await fetch(url, { headers: DEFAULT_HEADERS });
    const data = await handleResponse<any[]>(res);
    
    // Map to OpportunitySummary
    return data.map((item) => ({
      id: item.id,
      opportunity_id: item.id,
      case_id: item.case_id,
      case_number: item.case_number || 'N/A',
      decedent: item.decedent || 'Unknown Estate',
      decedent_name: item.decedent || 'Unknown Estate',
      estate_name: item.estate_name || `Estate of ${item.decedent || item.id.substring(0, 8)}`,
      county_id: item.county_id,
      county_name: item.county_name || item.county_id,
      workflow_stage: item.workflow_stage,
      lifecycle_stage: item.lifecycle_stage,
      score: item.score || 0,
      composite_viability_score: item.score || 0,
      priority: item.priority || 'PRIORITY_B',
      priority_tier: item.priority === 'HIGH' ? 'PRIORITY_A' : item.priority === 'LOW' ? 'PRIORITY_C' : (item.priority as any),
      authority_status: item.authority_status || 'TIER_4_UNRESOLVED',
      is_qc_certified: item.is_qc_certified !== undefined ? item.is_qc_certified : (item.workflow_stage === 'READY' || item.workflow_stage === 'DELIVERED'),
    }));
  },

  async getOpportunityWorkbench(id: string): Promise<FullPOFDossier> {
    const res = await fetch(`${API_BASE}/opportunities/${id}/workbench`, { headers: DEFAULT_HEADERS });
    return handleResponse<FullPOFDossier>(res);
  },

  async auditQualityControl(id: string): Promise<QualityControlAuditSummary> {
    const res = await fetch(`${API_BASE}/opportunities/${id}/qc`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
    });
    return handleResponse<QualityControlAuditSummary>(res);
  },

  async transitionFSM(id: string, targetStage: string, notes?: string): Promise<{ opportunity_id: string; workflow_stage: string }> {
    const res = await fetch(`${API_BASE}/opportunities/${id}/fsm`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ target_stage: targetStage, notes }),
    });
    return handleResponse<{ opportunity_id: string; workflow_stage: string }>(res);
  },

  async deliverOpportunity(id: string, notes?: string): Promise<OpportunitySummary> {
    const res = await fetch(`${API_BASE}/opportunities/${id}/deliver`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ notes }),
    });
    return handleResponse<OpportunitySummary>(res);
  },

  // Cases
  async getCases(countyId?: string): Promise<CaseItem[]> {
    const url = countyId ? `${API_BASE}/cases?county_id=${countyId}` : `${API_BASE}/cases`;
    const res = await fetch(url, { headers: DEFAULT_HEADERS });
    return handleResponse<CaseItem[]>(res);
  },

  async triggerScraper(countyFips: string, lookbackDays: number = 7): Promise<{
    status: string;
    county_fips: string;
    cases_ingested_count: number;
    message: string;
  }> {
    const res = await fetch(`${API_BASE}/cases/ingest`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ county_fips: countyFips, lookback_days: lookbackDays }),
    });
    return handleResponse<any>(res);
  },

  // Exceptions
  async getExceptions(): Promise<ExceptionItem[]> {
    const res = await fetch(`${API_BASE}/exceptions`, { headers: DEFAULT_HEADERS });
    return handleResponse<ExceptionItem[]>(res);
  },

  async resolveException(id: string, resolutionText: string): Promise<ExceptionItem> {
    const res = await fetch(`${API_BASE}/exceptions/${id}/resolve?resolution_text=${encodeURIComponent(resolutionText)}`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
    });
    return handleResponse<ExceptionItem>(res);
  },

  // Counties & Radar
  async getCountyBoard(): Promise<any[]> {
    try {
      const res = await fetch(`${API_BASE}/dashboard/county-board`, { headers: DEFAULT_HEADERS });
      return await handleResponse<any[]>(res);
    } catch {
      return [];
    }
  },

  async getCounties(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/counties`, { headers: DEFAULT_HEADERS });
    return handleResponse<any[]>(res);
  },

  // AI Investigator
  async investigateAI(prompt: string, opportunityId?: string): Promise<{ response: string; narrative?: string; timestamp?: string }> {
    const res = await fetch(`${API_BASE}/ai/investigate`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ prompt, opportunity_id: opportunityId || undefined }),
    });
    return handleResponse<any>(res);
  },

  // CRM Webhook Export
  async exportCrm(id: string, webhookUrl?: string, platform?: string): Promise<{ status: string; crm_webhook_acknowledged: boolean; message?: string }> {
    const res = await fetch(`${API_BASE}/opportunities/${id}/export-crm`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({
        webhook_url: webhookUrl || undefined,
        crm_platform: platform || 'GoHighLevel',
      }),
    });
    return handleResponse<any>(res);
  },
};
