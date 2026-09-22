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
  LifecycleStage,
  PriorityTier,
  AuthorityTier,
  CountyJurisdiction,
} from '../types';

// Domain Identifier Types (Branded Types to eliminate Primitive Obsession)
declare const __brand: unique symbol;
export type Brand<T, B> = T & { readonly [__brand]?: B };

export type OpportunityId = Brand<string, 'OpportunityId'>;
export type CountyId = Brand<string, 'CountyId'>;
export type CountyFips = Brand<string, 'CountyFips'>;
export type ExceptionId = Brand<string, 'ExceptionId'>;
export type CaseId = Brand<string, 'CaseId'>;

export type CrmPlatform = 'GoHighLevel' | 'HubSpot' | 'Salesforce' | string;

const API_BASE = '/api/v1';

const DEFAULT_HEADERS: Record<string, string> = {
  'Content-Type': 'application/json',
  'x-clerk-user-id': 'user_internal_operator',
  'x-clerk-role': 'Platform Admin',
};

// Domain DTOs and Request / Response Value Objects
export interface OpportunityFilterParams {
  stage?: LifecycleStage | string;
  county_id?: CountyId;
  authority_status?: AuthorityTier | string;
}

export interface TransitionFsmParams {
  id: OpportunityId;
  targetStage: LifecycleStage | string;
  notes?: string;
}

export interface DeliverOpportunityParams {
  id: OpportunityId;
  notes?: string;
}

export interface TriggerScraperParams {
  countyFips: CountyFips;
  lookbackDays?: number;
}

export interface ResolveExceptionParams {
  id: ExceptionId;
  resolutionText: string;
}

export interface AiInvestigateParams {
  prompt: string;
  opportunityId?: OpportunityId;
}

export interface CrmExportParams {
  id?: OpportunityId;
  webhookUrl?: string;
  platform?: CrmPlatform;
}

export interface FsmTransitionResult {
  opportunity_id: OpportunityId;
  workflow_stage: LifecycleStage | string;
}

export interface ScraperTriggerResult {
  status: string;
  county_fips: CountyFips;
  cases_ingested_count: number;
  message: string;
}

export interface AiInvestigationResult {
  response: string;
  narrative?: string;
  timestamp?: string;
}

export interface CrmExportResult {
  status: string;
  crm_webhook_acknowledged: boolean;
  message?: string;
}

export interface CountyBoardMetric {
  county_id: CountyId;
  name: string;
  state: string;
  status: string;
  tier: number;
  cases_count: number;
  opportunities_count: number;
  court_portal?: string;
  median_home_price?: number;
  est_inventory_pipeline_volume?: number;
  [key: string]: unknown;
}

export interface RawOpportunityApiItem {
  id: OpportunityId;
  case_id: CaseId;
  case_number?: string;
  decedent?: string;
  estate_name?: string;
  county_id: CountyId;
  county_name?: string;
  workflow_stage: LifecycleStage | string;
  lifecycle_stage?: LifecycleStage;
  score?: number;
  priority?: string;
  authority_status?: string;
  is_qc_certified?: boolean;
  [key: string]: unknown;
}

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

const PRIORITY_TIER_MAP: Record<string, PriorityTier> = {
  HIGH: 'PRIORITY_A',
  LOW: 'PRIORITY_C',
};

const mapPriorityTier = (priority?: string): PriorityTier => {
  if (!priority) return 'PRIORITY_B';
  return (PRIORITY_TIER_MAP[priority] || priority) as PriorityTier;
};

const resolveQcStatus = (isQcCertified?: boolean, workflowStage?: LifecycleStage | string): boolean => {
  if (isQcCertified !== undefined) {
    return isQcCertified;
  }
  return workflowStage === 'READY' || workflowStage === 'DELIVERED';
};

const resolveEstateName = (estateName?: string, decedent?: string, id = ''): string => {
  if (estateName) {
    return estateName;
  }
  const identifier = decedent || id.substring(0, 8);
  return `Estate of ${identifier}`;
};

const fallback = <T>(value: T | null | undefined, defaultValue: T): T => value || defaultValue;

const mapOpportunityItem = (item: RawOpportunityApiItem): OpportunitySummary => {
  const decedent = fallback(item.decedent, 'Unknown Estate');
  const score = fallback(item.score, 0);
  const priority = fallback(item.priority, 'PRIORITY_B');

  return {
    id: item.id,
    opportunity_id: item.id,
    case_id: item.case_id,
    case_number: fallback(item.case_number, 'N/A'),
    decedent,
    decedent_name: decedent,
    estate_name: resolveEstateName(item.estate_name, item.decedent, item.id),
    county_id: item.county_id,
    county_name: fallback(item.county_name, item.county_id),
    workflow_stage: item.workflow_stage,
    lifecycle_stage: item.lifecycle_stage,
    score,
    composite_viability_score: score,
    priority,
    priority_tier: mapPriorityTier(priority),
    authority_status: fallback(item.authority_status, 'TIER_4_UNRESOLVED'),
    is_qc_certified: resolveQcStatus(item.is_qc_certified, item.workflow_stage),
  };
};

export const ApiService = {
  // Opportunities
  async getOpportunities(params?: OpportunityFilterParams): Promise<OpportunitySummary[]> {
    const query = new URLSearchParams();
    if (params?.stage) query.append('workflow_stage', params.stage);
    if (params?.county_id) query.append('county_id', params.county_id);
    if (params?.authority_status) query.append('authority_status', params.authority_status);

    const url = `${API_BASE}/opportunities${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await fetch(url, { headers: DEFAULT_HEADERS });
    const data = await handleResponse<RawOpportunityApiItem[]>(res);
    return data.map(mapOpportunityItem);
  },

  async getOpportunityWorkbench(id: OpportunityId): Promise<FullPOFDossier> {
    const res = await fetch(`${API_BASE}/opportunities/${id}/workbench`, { headers: DEFAULT_HEADERS });
    return handleResponse<FullPOFDossier>(res);
  },

  async auditQualityControl(id: OpportunityId): Promise<QualityControlAuditSummary> {
    const res = await fetch(`${API_BASE}/opportunities/${id}/qc`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
    });
    return handleResponse<QualityControlAuditSummary>(res);
  },

  async transitionFSM(
    paramsOrId: OpportunityId | TransitionFsmParams,
    targetStage?: LifecycleStage | string,
    notes?: string
  ): Promise<FsmTransitionResult> {
    const id = typeof paramsOrId === 'object' ? paramsOrId.id : paramsOrId;
    const stage = typeof paramsOrId === 'object' ? paramsOrId.targetStage : targetStage;
    const noteText = typeof paramsOrId === 'object' ? paramsOrId.notes : notes;

    const res = await fetch(`${API_BASE}/opportunities/${id}/fsm`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ target_stage: stage, notes: noteText }),
    });
    return handleResponse<FsmTransitionResult>(res);
  },

  async deliverOpportunity(
    paramsOrId: OpportunityId | DeliverOpportunityParams,
    notes?: string
  ): Promise<OpportunitySummary> {
    const id = typeof paramsOrId === 'object' ? paramsOrId.id : paramsOrId;
    const noteText = typeof paramsOrId === 'object' ? paramsOrId.notes : notes;

    const res = await fetch(`${API_BASE}/opportunities/${id}/deliver`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ notes: noteText }),
    });
    return handleResponse<OpportunitySummary>(res);
  },

  // Cases
  async getCases(countyId?: CountyId): Promise<CaseItem[]> {
    const url = countyId ? `${API_BASE}/cases?county_id=${countyId}` : `${API_BASE}/cases`;
    const res = await fetch(url, { headers: DEFAULT_HEADERS });
    return handleResponse<CaseItem[]>(res);
  },

  async triggerScraper(
    paramsOrFips: CountyFips | TriggerScraperParams,
    lookbackDays: number = 7
  ): Promise<ScraperTriggerResult> {
    const fips = typeof paramsOrFips === 'object' ? paramsOrFips.countyFips : paramsOrFips;
    const lookback = typeof paramsOrFips === 'object' ? (paramsOrFips.lookbackDays ?? 7) : lookbackDays;

    const res = await fetch(`${API_BASE}/cases/ingest`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ county_fips: fips, lookback_days: lookback }),
    });
    return handleResponse<ScraperTriggerResult>(res);
  },

  // Exceptions
  async getExceptions(): Promise<ExceptionItem[]> {
    const res = await fetch(`${API_BASE}/exceptions`, { headers: DEFAULT_HEADERS });
    return handleResponse<ExceptionItem[]>(res);
  },

  async resolveException(
    paramsOrId: ExceptionId | ResolveExceptionParams,
    resolutionText?: string
  ): Promise<ExceptionItem> {
    const id = typeof paramsOrId === 'object' ? paramsOrId.id : paramsOrId;
    const text = typeof paramsOrId === 'object' ? paramsOrId.resolutionText : (resolutionText || '');

    const res = await fetch(
      `${API_BASE}/exceptions/${id}/resolve?resolution_text=${encodeURIComponent(text)}`,
      {
        method: 'POST',
        headers: DEFAULT_HEADERS,
      }
    );
    return handleResponse<ExceptionItem>(res);
  },

  // Counties & Radar
  async getCountyBoard(): Promise<CountyBoardMetric[]> {
    try {
      const res = await fetch(`${API_BASE}/dashboard/county-board`, { headers: DEFAULT_HEADERS });
      return await handleResponse<CountyBoardMetric[]>(res);
    } catch {
      return [];
    }
  },

  async getCounties(): Promise<CountyJurisdiction[]> {
    const res = await fetch(`${API_BASE}/counties`, { headers: DEFAULT_HEADERS });
    return handleResponse<CountyJurisdiction[]>(res);
  },

  // AI Investigator
  async investigateAI(
    paramsOrPrompt: string | AiInvestigateParams,
    opportunityId?: OpportunityId
  ): Promise<AiInvestigationResult> {
    const prompt = typeof paramsOrPrompt === 'object' ? paramsOrPrompt.prompt : paramsOrPrompt;
    const oppId = typeof paramsOrPrompt === 'object' ? paramsOrPrompt.opportunityId : opportunityId;

    const res = await fetch(`${API_BASE}/ai/investigate`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({ prompt, opportunity_id: oppId || undefined }),
    });
    return handleResponse<AiInvestigationResult>(res);
  },

  // CRM Webhook Export
  async exportCrm(
    idOrParams: OpportunityId | CrmExportParams,
    webhookUrl?: string,
    platform?: CrmPlatform
  ): Promise<CrmExportResult> {
    const id = typeof idOrParams === 'object' ? idOrParams.id! : idOrParams;
    const url = typeof idOrParams === 'object' ? idOrParams.webhookUrl : webhookUrl;
    const plat = typeof idOrParams === 'object' ? idOrParams.platform : platform;

    const res = await fetch(`${API_BASE}/opportunities/${id}/export-crm`, {
      method: 'POST',
      headers: DEFAULT_HEADERS,
      body: JSON.stringify({
        webhook_url: url || undefined,
        crm_platform: plat || 'GoHighLevel',
      }),
    });
    return handleResponse<CrmExportResult>(res);
  },
};
