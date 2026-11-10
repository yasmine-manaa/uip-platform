// ============================================================
// UIP Platform — TypeScript Type Definitions
// Aligned with backend API responses
// ============================================================

export type CaseStatus =
  | 'DRAFT'
  | 'ANALYZED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'MODIFIED'
  | 'ESCALATED'
  | 'CLOSED';

export type RiskTier = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type AlertSeverity = 'CRITICAL' | 'WARNING' | 'INFO';
export type DecisionCode =
  | 'PROCEED_STANDARD'
  | 'SPECIAL_TERMS_OFFER'
  | 'REQUEST_ADDITIONAL_INFO'
  | 'REQUIRE_SENIOR_REVIEW'
  | 'ANALYSIS_IMPOSSIBLE';

// ---- Case ----
export interface Case {
  id: string;
  reference: string;
  status: CaseStatus;
  applicant_name: string;
  coverage_requested?: string;
  risk_tier?: RiskTier;
  pure_premium_eur?: number;
  decision_code?: DecisionCode;
  provisional_recommendation?: string;
  created_at: string;
  updated_at: string;
  raw_input?: Record<string, unknown>;
}

export interface CaseCreate {
  applicant: {
    full_name: string;
    driver_age: number;
    licence_years: number;
    usage: string;
    postal_code: string;
    annual_mileage?: number;
  };
  vehicle: {
    vehicle_model: string;
    vehicle_power: number;
    vehicle_age: number;
    vehicle_genre: string;
    license_plate?: string;
  };
  claims_summary: {
    bonus_malus: number;
    prior_claims_count: number;
    cancelled_by_previous_insurer?: boolean;
  };
  coverage_requested: string;
  area_density?: number;
}

// ---- Document ----
export interface DocumentRecord {
  id: string;
  case_id: string;
  filename: string;
  doc_type: string;
  doc_label: string;
  page_count: number;
  ocr_status: string;
  confidence: number;
  extracted_fields: ExtractedField[];
  uploaded_at: string;
}

export interface ExtractedField {
  field_name: string;
  label: string;
  value: unknown;
  confidence: number;
  doc_id: string;
  page: number;
  status: string;
}

// ---- Agent ----
export interface AgentEvidence {
  key: string;
  value: unknown;
  source_ref?: string;
  confidence?: number;
}

export interface AgentAlert {
  code: string;
  severity: AlertSeverity;
  message: string;
  action_required?: string;
}

export interface AgentOutput {
  agent_id: string;
  agent_name: string;
  version: string;
  status: 'SUCCESS' | 'WARNING' | 'ESCALATED' | 'DATA_DEFICIENT';
  confidence_score: number;
  findings: string[];
  evidence: AgentEvidence[];
  sources: CitationRef[];
  missing_fields: string[];
  alerts: AgentAlert[];
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface CitationRef {
  citation_id: string;
  doc_id: string;
  doc_title: string;
  page: number;
  article: string;
  snippet: string;
  relevance_score: number;
}

// ---- Analysis / Decision ----
export interface RiskDimension {
  score: number;
  label: string;
  details: string;
}

export interface Decision {
  decision_code: DecisionCode;
  decision_title?: string;
  risk_tier: RiskTier;
  pure_premium_estimate?: number;
  confidence_level: number;
  favorable_factors: string[];
  unfavorable_factors: string[];
  required_actions: string[];
  justification: string;
  dimensions?: {
    actuarial_risk_level: RiskTier;
    data_quality: string;
    model_uncertainty: string;
  };
  timestamp: string;
}

// ---- Analysis Status ----
export interface AnalysisStatus {
  case_id: string;
  status: CaseStatus;
  decision_code?: DecisionCode;
  risk_tier?: RiskTier;
  agents_completed: number;
  updated_at: string;
}

export interface AnalysisFindings {
  case_id: string;
  status: string;
  agent_outputs: Record<string, AgentOutput>;
  contradictions: string[];
  escalation_required: boolean;
  provisional_decision: Decision;
  execution_timeline: ExecutionStep[];
  completed_at: string;
}

export interface ExecutionStep {
  step: string;
  description: string;
  timestamp: string;
}

// ---- Audit ----
export interface AuditEvent {
  id: string;
  case_id: string;
  event_type: string;
  actor: string;
  details: Record<string, unknown>;
  previous_hash: string;
  current_hash: string;
  timestamp: string;
}

export interface AuditTrail {
  case_id: string;
  is_chain_intact: boolean;
  total_events: number;
  events: AuditEvent[];
}

// ---- Human Review ----
export interface HumanReview {
  id: string;
  case_id: string;
  underwriter_name: string;
  underwriter_role: string;
  decision: string;
  final_premium_eur?: number;
  technical_loading_pct?: number;
  deductible_eur?: number;
  justification: string;
  special_conditions?: string;
  reviewed_at: string;
}

export interface HumanReviewCreate {
  underwriter_name: string;
  underwriter_role?: string;
  decision: string;
  final_premium_eur?: number;
  technical_loading_pct?: number;
  deductible_eur?: number;
  justification: string;
  special_conditions?: string;
}

// ---- Benchmarks ----
export interface BenchmarkConfig {
  config_id: string;
  name: string;
  description: string;
  glm_frequency: boolean;
  glm_severity: boolean;
  ml_boost: boolean;
  rag_citations: boolean;
  multi_agent: boolean;
}

export interface BenchmarkMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  citation_coverage: number;
  explainability_score: number;
  processing_time_ms: number;
  pure_premium_mae?: number;
  gini_coefficient?: number;
}

export interface BenchmarkResult {
  config: BenchmarkConfig;
  metrics: BenchmarkMetrics;
  sample_size: number;
  timestamp: string;
}

export interface ScientificValidation {
  results: BenchmarkResult[];
  conclusion: string;
  recommended_config: string;
  timestamp: string;
}

// ---- Client ----
export interface Client {
  id: string;
  client_reference: string;
  full_name: string;
  birth_date?: string;
  driver_age?: number;
  licence_number?: string;
  email?: string;
  phone?: string;
  address?: string;
  postal_code?: string;
  city?: string;
  created_at: string;
  updated_at: string;
}

export interface ClientCreate {
  full_name: string;
  birth_date?: string;
  driver_age?: number;
  licence_number?: string;
  email?: string;
  phone?: string;
  address?: string;
  postal_code?: string;
  city?: string;
}

export interface ClientUpdate extends Partial<ClientCreate> {}

export interface ClientHistory {
  id: string;
  client_id: string;
  event_type: string;
  event_date: string;
  details?: string;
  previous_bonus_malus?: number;
  new_bonus_malus?: number;
  created_at: string;
}

export interface ClientHistoryCreate {
  event_type: string;
  details?: string;
  previous_bonus_malus?: number;
  new_bonus_malus?: number;
}

// ---- Dataset ----
export interface DatasetStats {
  total_policies: number;
  total_claims: number;
  avg_claims_per_policy: number;
  avg_claim_amount: number;
  max_claim_amount: number;
  min_claim_amount: number;
  driver_age_range: [number, number];
  vehicle_power_range: [number, number];
  bonus_malus_range: [number, number];
  regions: number;
  brands: number;
  feature_stats: {
    driver_age: { mean: number; std: number; min: number; max: number };
    vehicle_power: { mean: number; std: number; min: number; max: number };
    vehicle_age: { mean: number; std: number; min: number; max: number };
    bonus_malus: { mean: number; std: number; min: number; max: number };
    area_density: { mean: number; std: number; min: number; max: number };
  };
  claim_stats: {
    total_claims: number;
    avg_claims_per_policy: number;
    claim_frequency: number;
    total_claim_amount: number;
    avg_claim_amount: number;
    max_claim_amount: number;
  };
  top_regions: Record<string, number>;
  top_brands: Record<string, number>;
  dataset_source: string;
  total_records: number;
}

export interface DatasetSample {
  sample_size: number;
  columns: string[];
  data: Record<string, unknown>[];
}

// ---- System ----
export interface SystemHealth {
  status: 'UP' | 'DOWN';
  service: string;
  version: string;
  actuarial_model_version: string;
}
