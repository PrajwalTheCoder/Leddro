export type WebsiteCondition = 
  | 'active'
  | 'not_listed'
  | 'unreachable'
  | 'dns_error'
  | 'ssl_expired'
  | 'broken_pages'
  | 'verification_required'
  | 'verified_accessible'
  | 'verification_failed';

export type ProspectStatus = 
  | 'new'
  | 'needs_audit'
  | 'needs_review'
  | 'draft_ready'
  | 'contacted'
  | 'archived';

export type SeverityLevel = 'high' | 'medium' | 'low' | 'info';

export interface Finding {
  id: string;
  prospectId: string;
  title: string;
  severity: SeverityLevel;
  observed: string;
  evidence: string;
  whyItMatters: string;
  recommendedAction: string;
  confidence: number;
  category: 'security' | 'reachability' | 'performance' | 'seo_meta' | 'conversion';
  httpStatus?: number;
  responseTimeMs?: number;
  checkStatus?: 'PASS' | 'WARNING' | 'FAIL' | 'ERROR' | 'NOT_CHECKED';
  checkedUrl?: string;
}

export interface AuditReport {
  id: string;
  prospectId: string;
  url?: string;
  timestamp: string;
  status: 'completed' | 'running' | 'failed';
  overallScore: number;
  findings: Finding[];
  rawDns: {
    aRecord: string;
    mxRecord: string;
    responseMs: number;
    nameservers: string[];
  };
  rawSsl: {
    valid: boolean;
    issuer: string;
    expiresDays: number;
    tlsVersion: string;
    cipher: string;
  };
  performance: {
    ttfbMs: number;
    domReadyMs: number;
    pageSizeKb: number;
    mobileViewportPresent: boolean;
  };
  headers: Record<string, string>;
}

export interface ScoringEvidence {
  findingId?: string;
  title: string;
  severity: string;
  category?: string;
  observed?: string;
  contribution: number;
}

export interface ScoringFactor {
  key: string;
  label: string;
  contribution: number;
  maxContribution: number;
  status: string;
  nature?: 'confirmed_deficiency' | 'potential_opportunity' | 'unknown' | 'failed_diagnostic' | 'informational' | string;
  summary: string;
  evidence: ScoringEvidence[];
}

export interface SeveritySummary {
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface ProspectScoringExplanation {
  opportunityScore: number;
  scoreVersion: string;
  confidenceScore: number;
  priorityLabel: 'High' | 'Medium' | 'Low' | 'Needs Audit';
  contactReadiness: 'verified' | 'unverified' | 'absent' | 'unknown';
  auditStatus: 'completed' | 'failed' | 'running' | 'none';
  auditAgeDays: number | null;
  auditTimestamp: string | null;
  severitySummary: SeveritySummary;
  factors: ScoringFactor[];
  limitations: string[];
  recommendedActions: string[];
}

export interface Prospect {
  id: string;
  name: string;
  category: string;
  location: {
    city: string;
    state: string;
    country: string;
  };
  websiteUrl?: string;
  websiteStatus: WebsiteCondition;
  opportunityScore: number;
  scoreBreakdown: {
    technicalUrgency: number;
    commercialIntent: number;
    resolutionEase: number;
  };
  status: ProspectStatus;
  lastActivity: string;
  phone?: string;
  email?: string;
  auditCount: number;
  latestAuditId?: string;
  tags: string[];
  recommendedAction: string;
  notes?: string;
  sourceProvider?: string;
  sourceRecordId?: string;
  sourceUrl?: string;
  discoveredAt?: string;
  lastVerifiedAt?: string;
  scoring?: ProspectScoringExplanation;
}

export interface DiscoveryResultItem {
  id: string;
  name: string;
  category: string;
  location: {
    city: string;
    state: string;
    country: string;
    address?: string;
    latitude?: number;
    longitude?: number;
  };
  website_url?: string;
  website_status: WebsiteCondition;
  phone?: string;
  email?: string;
  source_provider: string;
  source_record_id?: string;
  source_url?: string;
  attribution: string;
  is_saved: boolean;
  matched_existing_id?: string;
  duplicate_reason?: string;
  opportunity_score: number;
  score_urgency: number;
  score_intent: number;
  score_ease: number;
  tags: string[];
  raw_metadata?: Record<string, any>;
}

export interface ProviderConfigStatus {
  provider_id: string;
  name: string;
  is_configured: boolean;
  status_message: string;
  supported_filters: string[];
  attribution: string;
  data_retention_policy: string;
  rate_limit_info: string;
  requires_api_key: boolean;
}

export interface DiscoveryRunRecord {
  run_id: string;
  provider: string;
  params: {
    provider: string;
    category: string;
    country: string;
    region?: string;
    city?: string;
    limit: number;
    condition_filter?: string;
  };
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'PARTIAL' | 'FAILED' | 'CANCELLED';
  created_at: string;
  completed_at?: string;
  results_count: number;
  results: DiscoveryResultItem[];
  error_message?: string;
  partial_results: boolean;
  attribution: string;
  warnings: string[];
}

export type DraftStatus = 'draft' | 'edited' | 'approved' | 'awaiting_approval' | 'submitted' | 'failed' | 'cancelled' | 'uncertain';

export interface EmailDraft {
  id: string;
  prospectId: string;
  auditId?: string;
  recipientEmail: string;
  recipientName: string;
  subject: string;
  subjectAlternatives: string[];
  body: string;
  findingsReferenced: string[];
  aiClaimsRationale: {
    claim: string;
    findingId: string;
    rationale: string;
    evidenceType?: string;
  }[];
  outreachPurpose?: string;
  writingTone?: string;
  aiProvider?: string;
  aiModel?: string;
  generationMetadata?: {
    claims?: {
      claim: string;
      evidence_type: string;
      evidence_reference?: string;
      rationale?: string;
    }[];
    missing_information?: string[];
    needs_manual_review?: boolean;
    ai_provider?: string;
    ai_model?: string;
    custom_instructions?: string;
    regenerated?: boolean;
    [key: string]: any;
  };
  status: DraftStatus;
  createdAt: string;
  updatedAt: string;
  submittedAt?: string;
  providerMessageId?: string;
}

export interface AIProviderStatus {
  provider_id: string;
  name: string;
  is_configured: boolean;
  current_model: string;
  available_models: string[];
  status_message: string;
  is_active: boolean;
  is_local: boolean;
  is_free_tier?: boolean;
  data_transmission_notice: string;
}

export interface AISettings {
  active_provider: string;
  active_model: string;
  request_timeout: number;
  max_output_tokens: number;
  dev_name: string;
  dev_title: string;
  dev_services: string;
  dev_portfolio_url: string;
  dev_email: string;
  dev_signature: string;
  gemini_configured?: boolean;
  gemini_model?: string;
  gemini_masked_key?: string;
  openai_configured: boolean;
  openai_model: string;
  openai_masked_key: string;
  anthropic_configured: boolean;
  anthropic_model: string;
  anthropic_masked_key: string;
  compatible_configured: boolean;
  compatible_model: string;
  compatible_base_url: string;
}

export interface DraftGenerationPayload {
  prospect_id: string;
  audit_id?: string;
  purpose: 'website_improvement' | 'website_redesign' | 'new_website_proposal' | 'website_maintenance' | 'general_introduction';
  tone: 'professional' | 'friendly' | 'concise' | 'consultative';
  custom_instructions?: string;
  privacy_consent: boolean;
  provider_override?: string;
  model_override?: string;
}

export interface DraftRegenerationPayload {
  purpose?: 'website_improvement' | 'website_redesign' | 'new_website_proposal' | 'website_maintenance' | 'general_introduction';
  tone?: 'professional' | 'friendly' | 'concise' | 'consultative';
  custom_instructions?: string;
  privacy_consent: boolean;
  provider_override?: string;
  model_override?: string;
}


export interface EmailHistoryItem {
  id: string;
  recipient: string;
  prospectName: string;
  prospectId: string;
  subject: string;
  date: string;
  status: 'draft' | 'awaiting_approval' | 'submitted' | 'sent' | 'uncertain' | 'failed' | 'cancelled';
  provider: 'Gmail API (OAuth 2.0)' | 'Direct SMTP';
  providerMessageId?: string;
  bodySnippet: string;
  createdAt?: string;
}

export interface ActivityItem {
  id: string;
  type: 'audit' | 'import' | 'draft' | 'gmail' | 'status_change';
  title: string;
  description: string;
  timestamp: string;
  prospectId?: string;
}

export interface GoogleOAuthStatus {
  is_configured: boolean;
  missing_config: string[];
  is_connected: boolean;
  email: string | null;
  scopes: string[];
  last_verified: string | null;
  connected_at: string | null;
  expires_at: string | null;
  requires_reauth: boolean;
}

export interface EmailDispatchStatus {
  is_ready: boolean;
  method: 'oauth' | 'smtp' | 'none';
  provider_name: string;
  sender_email: string | null;
  smtp_configured: boolean;
  oauth_configured: boolean;
  smtp_host?: string;
  smtp_port?: number;
}

export interface EmailSendAttempt {
  id: string;
  draft_id: string;
  prospect_id?: string;
  recipient_email: string;
  sender_email: string;
  subject: string;
  status: 'awaiting_confirmation' | 'sending' | 'sent' | 'failed' | 'uncertain';
  gmail_message_id?: string;
  error_message?: string;
  error_code?: string;
  confirmed_at?: string;
  completed_at?: string;
  created_at?: string;
}

export interface SuppressionRecord {
  id: string;
  email_or_domain: string;
  reason: string;
  created_at?: string;
}

export interface IntegrationConfig {
  gmail: {
    isConfigured: boolean;
    missingConfig: string[];
    isConnected: boolean;
    connectedAccount?: string;
    scopes: string[];
    lastVerified?: string;
    connectedAt?: string;
    expiresAt?: string;
    requiresReauth?: boolean;
    sendQuotaRemaining?: number;
  };
  aiProvider: {
    provider: 'anthropic' | 'openai' | 'local_ollama';
    isConfigured: boolean;
    model: string;
    status: 'ready' | 'missing_key' | 'offline';
  };
  discoveryProvider: {
    provider: 'osm_overpass' | 'google_places' | 'custom_crawler';
    isConfigured: boolean;
    activeName: string;
    rateLimitRemaining: number;
  };
}

export type FindingComparisonState = 'resolved' | 'new' | 'persistent' | 'inconclusive';

export interface FindingComparisonItem {
  state: FindingComparisonState;
  checkKey: string;
  title: string;
  category: string;
  severity: SeverityLevel;
  olderFindingId?: string;
  newerFindingId?: string;
  olderEvidence?: string;
  newerEvidence?: string;
  olderObserved?: string;
  newerObserved?: string;
  reason: string;
}

export interface MeasurementComparisonItem {
  key: string;
  label: string;
  before: any;
  after: any;
  unit?: string;
  change?: number;
  changePercent?: number;
  direction: 'improved' | 'degraded' | 'unchanged' | 'neutral' | 'unknown';
  status: 'comparable' | 'inconclusive' | 'not_comparable';
  reason?: string;
}

export interface ComparisonSummary {
  resolvedCount: number;
  newCount: number;
  persistentCount: number;
  inconclusiveCount: number;
  comparableMeasurementsCount: number;
  totalFindingsEvaluated: number;
  isReliable: boolean;
  executionStatus: string;
}

export interface AuditComparisonResponse {
  olderAuditId: string;
  newerAuditId: string;
  olderTimestamp: string;
  newerTimestamp: string;
  url: string;
  prospectId?: string;
  prospectName?: string;
  executionStatus: 'both_completed' | 'newer_failed' | 'older_failed' | 'both_failed' | 'partial';
  isReliable: boolean;
  summary: ComparisonSummary;
  resolvedFindings: FindingComparisonItem[];
  newFindings: FindingComparisonItem[];
  persistentFindings: FindingComparisonItem[];
  inconclusiveFindings: FindingComparisonItem[];
  measurements: MeasurementComparisonItem[];
  limitations: string[];
}

export interface AuditCompareRequest {
  older_audit_id?: string;
  newer_audit_id?: string;
  olderAuditId?: string;
  newerAuditId?: string;
}

