/**
 * Gieni OS - Frontend Type Definitions & Data Transfer Objects (DTOs)
 * Strict typing matching Platform API specifications
 */

export type LifecycleStage =
  | 'DISCOVERED'
  | 'PROPERTY_IDENTIFIED'
  | 'OWNERSHIP_RESOLVED'
  | 'CONTROL_MAPPED'
  | 'AUTHORITY_RESOLVED'
  | 'SCORED'
  | 'QC_CERTIFIED'
  | 'DELIVERED'
  | 'CONTACTED'
  | 'APPOINTMENT'
  | 'OFFER'
  | 'CONTRACT'
  | 'CLOSED_WON'
  | 'CLOSED_LOST'
  | 'ARCHIVED';

export type PriorityTier = 'PRIORITY_A' | 'PRIORITY_B' | 'PRIORITY_C' | 'DISQUALIFIED';

export type AuthorityTier =
  | 'TIER_1_CONFIRMED'
  | 'TIER_2_LIKELY'
  | 'TIER_3_STAKEHOLDER_CONSENSUS'
  | 'TIER_4_UNRESOLVED';

export type ControlArchetype =
  | 'UNIFIED_FIDUCIARY'
  | 'INFORMAL_FAMILY_LEADER'
  | 'PROXY_CONTROLLER'
  | 'TRUST_FIDUCIARY'
  | 'CONTESTED_FACTIONS';

export interface OpportunitySummary {
  id: string;
  opportunity_id?: string;
  case_id: string;
  case_number: string;
  decedent?: string;
  decedent_name?: string;
  estate_name?: string;
  county_id: string;
  county_name?: string;
  apn?: string;
  street?: string;
  city?: string;
  workflow_stage: string;
  lifecycle_stage?: LifecycleStage;
  score: number;
  composite_viability_score?: number;
  deal_friction_score?: number;
  priority: string;
  priority_tier?: PriorityTier;
  authority_status: string;
  is_qc_certified?: boolean;
}

export interface GateCheckResult {
  gate_number: number;
  gate_name: string;
  passed: boolean;
  failure_reason: string | null;
  telemetry_metadata?: Record<string, unknown>;
}

export interface QualityControlAuditSummary {
  opportunity_id: string;
  is_fully_certified: boolean;
  failed_gate: number | null;
  gate_results: GateCheckResult[];
  disqualification_reason: string | null;
  current_lifecycle_stage: LifecycleStage | string;
  composite_viability_score: number;
  priority_tier: PriorityTier | string;
}

export interface ExceptionItem {
  id: string;
  opportunity_id: string;
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'NORMAL' | 'LOW';
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'DISMISSED';
  assignee: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  // Dynamic UI fields
  case_number?: string;
  failed_gate?: number;
  net_equity?: number;
  sla_hours_remaining?: number;
}

export interface CaseItem {
  id: string;
  case_number: string;
  county_id: string;
  decedent: string;
  filing_date: string;
  status: string;
}

export interface CountyJurisdiction {
  fips: string;
  name: string;
  vendor: string;
  lastIngested: string;
  volumeToday: number;
  status: 'IDLE' | 'RUNNING' | 'ERROR' | 'CAPTCHA_HALTED';
}

export interface PropertyProfile {
  apn: string;
  situs_address: string;
  city_state_zip: string;
  legal_description?: string;
  avm_market_estimate: number;
  total_assessed_value: number;
  land_value?: number;
  improvement_value?: number;
  landuse?: string;
  pas_score: number;
}

export interface OwnershipProfile {
  legal_title_vesting: string;
  ownership_complexity_score: number;
  net_distributable_equity: number;
  net_equity_pct: number;
  target_wholesale_mao: number;
  senior_mortgage_balance: number;
  municipal_liens: number;
  estimated_repairs: number;
  is_free_and_clear: boolean;
}

export interface AuthorityProfile {
  authority_tier: AuthorityTier | string;
  court_oversight_model: string;
  can_execute_psa: boolean;
  court_confirmation_required: boolean;
  statutory_basis: string;
  statutory_power_scope: string;
}

export interface RiskProfile {
  overall_deal_risk_classification: string;
  foreclosure_acceleration_risk: string;
  title_cloud_detected: boolean;
  contested_will_flag: boolean;
}

export interface EvidenceSummary {
  qc_certification_stamp: string | null;
  recorded_deed_instrument: string | null;
  source_dockets: string[];
  petition_pdf_sha256?: string;
  letters_pdf_sha256?: string;
  parcel_card_sha256?: string;
}

export interface ContactSummary {
  target_name: string;
  relationship: string;
  primary_phone: string | null;
  line_type: string | null;
  confidence_score: number;
  is_dnc: boolean;
  verified_email: string | null;
  mailing_address: string;
  heir_count?: number;
  skip_trace_status: string;
}

export interface RecommendedAction {
  transaction_strategy: string;
  first_touch_channel: string;
  conversational_framing_script: string;
}

export interface FullPOFDossier {
  opportunity: {
    id: string;
    case_id: string;
    case_number: string;
    decedent: string;
    estate_name?: string;
    county_id: string;
    county_name: string;
    workflow_stage: string;
    priority: string;
    authority_status: string;
    score: number;
  };
  property_summary: PropertyProfile;
  ownership_summary: OwnershipProfile;
  authority_summary: AuthorityProfile;
  risk_summary: RiskProfile;
  evidence_summary: EvidenceSummary;
  score_summary: {
    composite_viability_score: number;
    priority_tier: string;
    deal_friction_score: number;
    dispatch_sla: string;
  };
  contact_summary: ContactSummary;
  recommended_action: RecommendedAction;
}

export interface TelemetryEvent {
  type: string;
  message?: string;
  step?: string;
  fips?: string;
  timestamp: number;
  data?: Record<string, unknown>;
}
