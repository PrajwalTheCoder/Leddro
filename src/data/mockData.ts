import { Prospect, AuditReport, EmailDraft, EmailHistoryItem, ActivityItem, IntegrationConfig } from '../types';

export const INITIAL_PROSPECTS: Prospect[] = [];
export const MOCK_AUDIT_REPORTS: Record<string, AuditReport> = {};
export const INITIAL_EMAIL_DRAFTS: EmailDraft[] = [];
export const INITIAL_EMAIL_HISTORY: EmailHistoryItem[] = [];
export const INITIAL_ACTIVITIES: ActivityItem[] = [];

export const INITIAL_INTEGRATION_CONFIG: IntegrationConfig = {
  gmail: {
    isConfigured: false,
    missingConfig: [],
    isConnected: false,
    connectedAccount: undefined,
    scopes: [],
    lastVerified: undefined,
    sendQuotaRemaining: 500
  },
  aiProvider: {
    provider: 'anthropic',
    isConfigured: true,
    model: 'claude-3-7-sonnet-20250219',
    status: 'ready'
  },
  discoveryProvider: {
    provider: 'osm_overpass',
    isConfigured: true,
    activeName: 'OpenStreetMap Overpass + Local Registry Index',
    rateLimitRemaining: 9400
  }
};
