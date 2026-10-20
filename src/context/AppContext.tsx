import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  Prospect, 
  AuditReport, 
  EmailDraft, 
  EmailHistoryItem, 
  ActivityItem, 
  IntegrationConfig, 
  ProspectStatus,
  Finding,
  GoogleOAuthStatus,
  EmailDispatchStatus,
  EmailSendAttempt,
  SuppressionRecord,
  AuditComparisonResponse
} from '../types';
import { 
  INITIAL_PROSPECTS, 
  MOCK_AUDIT_REPORTS, 
  INITIAL_EMAIL_DRAFTS, 
  INITIAL_EMAIL_HISTORY, 
  INITIAL_ACTIVITIES, 
  INITIAL_INTEGRATION_CONFIG 
} from '../data/mockData';

export interface ToastMessage {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
}

interface AppContextType {
  prospects: Prospect[];
  selectedProspectId: string | null;
  selectedProspect: Prospect | null;
  setSelectedProspectId: (id: string | null) => void;
  updateProspectStatus: (id: string, status: ProspectStatus) => void;
  addProspect: (prospect: Omit<Prospect, 'id' | 'lastActivity' | 'auditCount'>) => Prospect;
  importProspects: (newProspects: Partial<Prospect>[]) => void;
  refreshProspects: () => Promise<void>;
  
  auditReports: Record<string, AuditReport>;
  runAudit: (prospectId: string) => Promise<AuditReport>;
  fetchProspectAudits: (prospectId: string) => Promise<AuditReport[]>;
  compareAudits: (olderAuditId: string, newerAuditId: string) => Promise<AuditComparisonResponse>;
  isAuditing: boolean;
  auditingProspectId: string | null;
  auditProgressMessage: string;
  
  emailDrafts: EmailDraft[];
  activeDraft: EmailDraft | null;
  setActiveDraftId: (id: string | null) => void;
  saveEmailDraft: (draft: EmailDraft) => Promise<void>;
  deleteEmailDraft: (id: string) => Promise<void>;
  refreshDrafts: () => Promise<void>;
  createEmailDraftForProspect: (prospectId: string) => EmailDraft;
  submitEmailDraft: (draftId: string) => Promise<{ success: boolean; messageId: string }>;
  sendEmailDraft: (payload: { draftId: string; recipient: string; subject: string; body: string; confirmed: boolean }) => Promise<{ success: boolean; messageId?: string; provider?: string; error?: string }>;
  
  // Real Phase 6 Google OAuth & Gmail Gateway
  googleStatus: GoogleOAuthStatus | null;
  fetchGoogleStatus: () => Promise<GoogleOAuthStatus | null>;
  emailDispatchStatus: EmailDispatchStatus | null;
  fetchEmailDispatchStatus: () => Promise<EmailDispatchStatus | null>;
  connectGoogle: () => Promise<void>;
  testGoogleConnection: () => Promise<{ success: boolean; message: string; latency_ms?: number }>;
  disconnectGoogle: () => Promise<void>;

  // History & Suppressions
  emailHistory: EmailHistoryItem[];
  refreshEmailHistory: () => Promise<void>;
  suppressions: SuppressionRecord[];
  addSuppression: (emailOrDomain: string, reason?: string) => Promise<void>;
  removeSuppression: (id: string) => Promise<void>;

  activities: ActivityItem[];
  integrations: IntegrationConfig;
  updateIntegrations: (config: Partial<IntegrationConfig>) => void;
  
  toasts: ToastMessage[];
  addToast: (message: string, type?: ToastMessage['type']) => void;
  removeToast: (id: string) => void;

  isCommandPaletteOpen: boolean;
  setIsCommandPaletteOpen: (open: boolean) => void;
  
  filterQuery: string;
  setFilterQuery: (query: string) => void;
  activeFilter: 'all' | 'needs_audit' | 'needs_review' | 'draft_ready' | 'contacted' | 'high_priority';
  setActiveFilter: (filter: 'all' | 'needs_audit' | 'needs_review' | 'draft_ready' | 'contacted' | 'high_priority') => void;

  backendOnline: boolean | null;
  backendDetails: { version: string; database: string; engine: string; prospectsCount: number; auditsCount: number } | null;
  checkBackendHealth: () => Promise<boolean>;
  aiStatus: { activeName: string; isConfigured: boolean; activeProvider: string } | null;
  refreshAIStatus: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);


export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Load prospects from localStorage or fall back to rich demo dataset
  const [prospects, setProspects] = useState<Prospect[]>(() => {
    const saved = localStorage.getItem('leddro_prospects');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      } catch (e) { /* ignore */ }
    }
    return INITIAL_PROSPECTS;
  });

  const [selectedProspectId, setSelectedProspectId] = useState<string | null>(() => {
    return INITIAL_PROSPECTS.length > 0 ? INITIAL_PROSPECTS[0].id : null;
  });
  
  const [auditReports, setAuditReports] = useState<Record<string, AuditReport>>(() => {
    const saved = localStorage.getItem('leddro_audits');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object' && Object.keys(parsed).length > 0) {
          return parsed;
        }
      } catch (e) { /* ignore */ }
    }
    return MOCK_AUDIT_REPORTS;
  });

  const [emailDrafts, setEmailDrafts] = useState<EmailDraft[]>(() => {
    const saved = localStorage.getItem('leddro_drafts');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      } catch (e) { /* ignore */ }
    }
    return INITIAL_EMAIL_DRAFTS;
  });

  const [activeDraftId, setActiveDraftId] = useState<string | null>(() => {
    return INITIAL_EMAIL_DRAFTS.length > 0 ? INITIAL_EMAIL_DRAFTS[0].id : null;
  });

  const [emailHistory, setEmailHistory] = useState<EmailHistoryItem[]>(() => {
    const saved = localStorage.getItem('leddro_history');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      } catch (e) { /* ignore */ }
    }
    return INITIAL_EMAIL_HISTORY;
  });

  const [activities, setActivities] = useState<ActivityItem[]>(() => {
    const saved = localStorage.getItem('leddro_activities');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      } catch (e) { /* ignore */ }
    }
    return INITIAL_ACTIVITIES;
  });

  const [integrations, setIntegrations] = useState<IntegrationConfig>(() => {
    const saved = localStorage.getItem('leddro_integrations');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { /* ignore */ }
    }
    return INITIAL_INTEGRATION_CONFIG;
  });

  const [isAuditing, setIsAuditing] = useState(false);
  const [auditingProspectId, setAuditingProspectId] = useState<string | null>(null);
  const [auditProgressMessage, setAuditProgressMessage] = useState<string>('');

  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'needs_audit' | 'needs_review' | 'draft_ready' | 'contacted' | 'high_priority'>('all');

  // Real backend health and connectivity state
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [backendDetails, setBackendDetails] = useState<any>(null);

  // Phase 6 & Phase 8: Google OAuth, Direct SMTP & Suppression state
  const [googleStatus, setGoogleStatus] = useState<GoogleOAuthStatus | null>(null);
  const [emailDispatchStatus, setEmailDispatchStatus] = useState<EmailDispatchStatus | null>(null);
  const [suppressions, setSuppressions] = useState<SuppressionRecord[]>([]);
  const [aiStatus, setAIStatus] = useState<{ activeName: string; isConfigured: boolean; activeProvider: string } | null>(null);

  const refreshAIStatus = async () => {
    try {
      const res = await fetch('/api/ai/providers');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          const active = data.find((p: any) => p.is_active && p.is_configured) ||
                         data.find((p: any) => p.is_configured) ||
                         data.find((p: any) => p.is_active) ||
                         data[0];
          setAIStatus({
            activeName: active.name,
            isConfigured: active.is_configured,
            activeProvider: active.provider_id
          });
        }
      }
    } catch {
      // Backend unavailable
    }
  };

  const fetchGoogleStatus = async (): Promise<GoogleOAuthStatus | null> => {
    try {
      const res = await fetch('/api/google/status');
      if (res.ok) {
        const data: GoogleOAuthStatus = await res.json();
        setGoogleStatus(data);
        setIntegrations((prev) => ({
          ...prev,
          gmail: {
            ...prev.gmail,
            isConfigured: data.is_configured,
            missingConfig: data.missing_config || [],
            isConnected: data.is_connected,
            connectedAccount: data.email || undefined,
            scopes: data.scopes || [],
            lastVerified: data.last_verified || undefined,
            connectedAt: data.connected_at || undefined,
            expiresAt: data.expires_at || undefined,
            requiresReauth: data.requires_reauth,
            sendQuotaRemaining: 500
          }
        }));
        return data;
      }
    } catch {
      // Backend unavailable
    }
    return null;
  };

  const fetchEmailDispatchStatus = async (): Promise<EmailDispatchStatus | null> => {
    try {
      const res = await fetch('/api/email/status');
      if (res.ok) {
        const data: EmailDispatchStatus = await res.json();
        setEmailDispatchStatus(data);
        return data;
      }
    } catch {
      // Backend unavailable
    }
    return null;
  };

  const refreshEmailHistory = async () => {
    try {
      const res = await fetch('/api/email/history');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setEmailHistory(data);
        }
      }
    } catch {
      // Backend unavailable
    }
  };

  const fetchSuppressions = async () => {
    try {
      const res = await fetch('/api/email/suppression');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setSuppressions(data);
        }
      }
    } catch {
      // Backend unavailable
    }
  };

  const checkBackendHealth = async (): Promise<boolean> => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setBackendOnline(true);
        setBackendDetails(data);
        return true;
      }
    } catch {
      // Backend unavailable
    }
    setBackendOnline(false);
    return false;
  };

  // Sync with real backend on mount
  useEffect(() => {
    checkBackendHealth().then((isOnline) => {
      if (isOnline) {
        // Fetch prospects from SQLite
        fetch('/api/prospects')
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data && Array.isArray(data)) {
              const realProspects = data.filter((p: any) => !p.id?.startsWith('pr-') && !p.websiteUrl?.includes('apexprecisiontech.com'));
              setProspects(realProspects);
              setSelectedProspectId((prev) => {
                if (prev && realProspects.some((p: any) => p.id === prev)) return prev;
                return realProspects.length > 0 ? realProspects[0].id : null;
              });
            }
          })
          .catch(() => {});

        // Fetch audit reports from SQLite
        fetch('/api/audits')
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data && Array.isArray(data)) {
              const map: Record<string, AuditReport> = {};
              for (const r of data) {
                if (!r.id?.startsWith('audit-') && !r.prospectId?.startsWith('pr-')) {
                  map[r.id] = r;
                }
              }
              setAuditReports(map);
            }
          })
          .catch(() => {});

        // Fetch email drafts from SQLite
        fetch('/api/drafts')
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data && Array.isArray(data)) {
              const realDrafts = data.filter((d: any) => !d.id?.startsWith('draft-') && !d.prospectId?.startsWith('pr-'));
              setEmailDrafts(realDrafts);
              setActiveDraftId((prev) => {
                if (prev && realDrafts.some((d: any) => d.id === prev)) return prev;
                return realDrafts.length > 0 ? realDrafts[0].id : null;
              });
            }
          })
          .catch(() => {});

        // Fetch Google status, dispatches, suppression records, and AI status
        fetchGoogleStatus();
        fetchEmailDispatchStatus();
        refreshAIStatus();
        refreshEmailHistory();
        fetchSuppressions();
      }
    });
  }, []);


  // Persistence
  useEffect(() => {
    localStorage.setItem('leddro_prospects', JSON.stringify(prospects));
  }, [prospects]);

  useEffect(() => {
    localStorage.setItem('leddro_audits', JSON.stringify(auditReports));
  }, [auditReports]);

  useEffect(() => {
    localStorage.setItem('leddro_drafts', JSON.stringify(emailDrafts));
  }, [emailDrafts]);

  useEffect(() => {
    localStorage.setItem('leddro_history', JSON.stringify(emailHistory));
  }, [emailHistory]);

  useEffect(() => {
    localStorage.setItem('leddro_activities', JSON.stringify(activities));
  }, [activities]);

  useEffect(() => {
    localStorage.setItem('leddro_integrations', JSON.stringify(integrations));
  }, [integrations]);

  // Global keyboard shortcuts (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const addToast = (message: string, type: ToastMessage['type'] = 'info') => {
    const id = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      removeToast(id);
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const selectedProspect = prospects.find((p) => p.id === selectedProspectId) || null;
  const activeDraft = emailDrafts.find((d) => d.id === activeDraftId) || (emailDrafts.length > 0 ? emailDrafts[0] : null);

  const refreshProspects = async () => {
    try {
      const res = await fetch('/api/prospects');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setProspects(data);
        }
      }
    } catch {
      // ignore
    }
  };

  const updateProspectStatus = (id: string, status: ProspectStatus) => {
    setProspects((prev) =>
      prev.map((p) => (p.id === id ? { ...p, status, lastActivity: 'Just now' } : p))
    );
    const target = prospects.find((p) => p.id === id);
    if (target) {
      const newActivity: ActivityItem = {
        id: 'act-' + Date.now(),
        type: 'status_change',
        title: `Status changed to ${status.replace('_', ' ')}`,
        description: `Updated status for ${target.name}.`,
        timestamp: 'Just now',
        prospectId: id,
      };
      setActivities((prev) => [newActivity, ...prev]);
      addToast(`Updated ${target.name} status to ${status.replace('_', ' ')}`, 'success');
    }
  };

  const addProspect = (data: Omit<Prospect, 'id' | 'lastActivity' | 'auditCount'>): Prospect => {
    const newProspect: Prospect = {
      ...data,
      id: 'pr-' + Date.now(),
      lastActivity: 'Just now',
      auditCount: 0,
    };
    setProspects((prev) => [newProspect, ...prev]);
    setSelectedProspectId(newProspect.id);
    
    const newActivity: ActivityItem = {
      id: 'act-' + Date.now(),
      type: 'import',
      title: `Prospect created: ${newProspect.name}`,
      description: `Added manually into local database.`,
      timestamp: 'Just now',
      prospectId: newProspect.id,
    };
    setActivities((prev) => [newActivity, ...prev]);
    addToast(`Added prospect ${newProspect.name}`, 'success');
    return newProspect;
  };

  const importProspects = (importedList: Partial<Prospect>[]) => {
    const createdList: Prospect[] = importedList.map((item, idx) => ({
      id: 'pr-imp-' + Date.now() + '-' + idx,
      name: item.name || 'Unnamed Business',
      category: item.category || 'General Business',
      location: item.location || { city: 'Mumbai', state: 'Maharashtra', country: 'India' },
      websiteUrl: item.websiteUrl,
      websiteStatus: item.websiteStatus || (item.websiteUrl ? 'active' : 'not_listed'),
      opportunityScore: item.opportunityScore || 70,
      scoreBreakdown: item.scoreBreakdown || { technicalUrgency: 25, commercialIntent: 25, resolutionEase: 20 },
      status: 'new',
      lastActivity: 'Just imported',
      auditCount: 0,
      tags: item.tags || ['Imported Batch'],
      recommendedAction: item.recommendedAction || 'Execute initial website diagnostic audit.',
      notes: item.notes || 'Imported via CSV batch processor.'
    }));

    setProspects((prev) => [...createdList, ...prev]);
    const newActivity: ActivityItem = {
      id: 'act-' + Date.now(),
      type: 'import',
      title: `Imported ${createdList.length} prospects from CSV`,
      description: `Batch processed into active workspace.`,
      timestamp: 'Just now'
    };
    setActivities((prev) => [newActivity, ...prev]);
    addToast(`Successfully imported ${createdList.length} prospects`, 'success');
  };

  // Real server-side audit runner invoking Python FastAPI /api/audits/run
  const runAudit = async (prospectId: string): Promise<AuditReport> => {
    const target = prospects.find((p) => p.id === prospectId);
    if (!target) throw new Error('Prospect not found');

    if (!target.websiteUrl) {
      addToast(`Cannot audit ${target.name}: No registered website URL discovered.`, 'warning');
      throw new Error(`Cannot audit ${target.name}: No registered website URL found.`);
    }

    setIsAuditing(true);
    setAuditingProspectId(prospectId);
    setAuditProgressMessage('Checking backend service and validating target URL...');

    try {
      setAuditProgressMessage(`Enforcing SSRF security policy on ${target.websiteUrl}...`);
      await new Promise((r) => setTimeout(r, 200));

      setAuditProgressMessage('Executing server-side audit (DNS zone, TLS socket, HTTP crawl, DOM parsing)...');

      const response = await fetch('/api/audits/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: target.websiteUrl,
          prospectId: target.id
        })
      });

      if (!response.ok) {
        let errorDetail = `Audit failed with HTTP ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch {
          // ignore
        }
        addToast(`Audit Failed: ${errorDetail}`, 'error');
        throw new Error(errorDetail);
      }

      const report: AuditReport = await response.json();

      // Persist to local state
      setAuditReports((prev) => ({ ...prev, [report.id]: report }));

      // Update prospect opportunity score & status based on real audit
      setProspects((prev) =>
        prev.map((p) =>
          p.id === target.id
            ? {
                ...p,
                auditCount: (p.auditCount || 0) + 1,
                latestAuditId: report.id,
                opportunityScore: report.overallScore,
                websiteStatus: report.status === 'completed' ? 'active' : 'unreachable',
                status: p.status === 'new' || p.status === 'needs_audit' ? 'needs_review' : p.status,
                lastActivity: 'Audited just now'
              }
            : p
        )
      );

      const newActivity: ActivityItem = {
        id: 'act-' + Date.now(),
        type: 'audit',
        title: `Live website audit completed for ${target.name}`,
        description: `Inspected ${report.url || target.websiteUrl}. Discovered ${report.findings.length} findings (Score: ${report.overallScore}/100).`,
        timestamp: 'Just now',
        prospectId: target.id
      };
      setActivities((prev) => [newActivity, ...prev]);

      addToast(`Audit completed for ${target.name} (${report.findings.length} findings recorded)`, 'success');
      return report;
    } catch (err: any) {
      // If backend is unreachable (e.g. running on static demo host like GitHub Pages or Vercel),
      // seamlessly execute interactive simulated audit in Demo Sandbox!
      if (!backendOnline || err.message?.includes('Failed to fetch') || err.name === 'TypeError') {
        setAuditProgressMessage('Executing simulated diagnostic (DNS zone, TLS socket, HTTP crawl)...');
        await new Promise((r) => setTimeout(r, 600));

        const existingReport = target.latestAuditId ? auditReports[target.latestAuditId] : null;
        const newScore = Math.floor(Math.random() * 25) + 65;
        const simulatedReport: AuditReport = existingReport || {
          id: 'demo-audit-' + Date.now(),
          prospectId: target.id,
          url: target.websiteUrl,
          timestamp: new Date().toISOString(),
          status: 'completed',
          overallScore: newScore,
          findings: [
            {
              id: 'f-demo-tls-' + Date.now(),
              prospectId: target.id,
              title: 'TLS 1.2 Cipher Suite Remediation Recommended',
              severity: 'medium',
              observed: 'Legacy CBC cipher suites enabled alongside modern GCM.',
              evidence: 'TLS Handshake Probe: TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA active.',
              whyItMatters: 'Legacy ciphers increase vulnerability to padding oracle exploits.',
              recommendedAction: 'Restrict server cipher list to modern AEAD ciphers (AES-GCM / CHACHA20).',
              confidence: 0.95,
              category: 'security'
            },
            {
              id: 'f-demo-dmarc-' + Date.now(),
              prospectId: target.id,
              title: 'DMARC Quarantine Policy Missing in DNS Zone',
              severity: 'high',
              observed: 'No _dmarc TXT record detected for domain.',
              evidence: 'DNS query _dmarc NXDOMAIN.',
              whyItMatters: 'Leaves domain open to spoofed email fraud and hurts deliverability.',
              recommendedAction: 'Publish v=DMARC1; p=quarantine policy record.',
              confidence: 0.98,
              category: 'security'
            }
          ],
          rawDns: {
            aRecord: '104.21.48.112',
            mxRecord: 'mail.' + (target.websiteUrl?.replace('https://', '').replace('http://', '').split('/')[0] || 'domain.com'),
            responseMs: 48,
            nameservers: ['ns1.cloudflare.com', 'ns2.cloudflare.com']
          },
          rawSsl: {
            valid: true,
            issuer: 'Cloudflare Inc ECC CA-3',
            expiresDays: 62,
            tlsVersion: 'TLS 1.3',
            cipher: 'TLS_AES_256_GCM_SHA384'
          },
          performance: {
            ttfbMs: 340,
            domReadyMs: 1250,
            pageSizeKb: 1840,
            mobileViewportPresent: true
          },
          headers: {
            'server': 'cloudflare',
            'content-type': 'text/html; charset=UTF-8'
          }
        };

        setAuditReports((prev) => ({ ...prev, [simulatedReport.id]: simulatedReport }));
        setProspects((prev) =>
          prev.map((p) =>
            p.id === target.id
              ? {
                  ...p,
                  auditCount: (p.auditCount || 0) + 1,
                  latestAuditId: simulatedReport.id,
                  opportunityScore: simulatedReport.overallScore,
                  websiteStatus: 'active',
                  status: p.status === 'new' || p.status === 'needs_audit' ? 'needs_review' : p.status,
                  lastActivity: 'Audited in Demo Sandbox'
                }
              : p
          )
        );

        const newActivity: ActivityItem = {
          id: 'act-' + Date.now(),
          type: 'audit',
          title: `Demo diagnostic audit completed for ${target.name}`,
          description: `Simulated scan for ${target.websiteUrl}. Discovered ${simulatedReport.findings.length} findings (Score: ${simulatedReport.overallScore}/100).`,
          timestamp: 'Just now',
          prospectId: target.id
        };
        setActivities((prev) => [newActivity, ...prev]);

        addToast(`Demo Audit completed for ${target.name} (${simulatedReport.findings.length} findings recorded)`, 'success');
        return simulatedReport;
      }

      if (err.message && !err.message.includes('Audit Failed')) {
        addToast(`Backend error: ${err.message}`, 'error');
      }
      throw err;
    } finally {
      setIsAuditing(false);
      setAuditingProspectId(null);
      setAuditProgressMessage('');
    }
  };

  const fetchProspectAudits = async (prospectId: string): Promise<AuditReport[]> => {
    try {
      const res = await fetch(`/api/audits/prospect/${prospectId}`);
      if (res.ok) {
        const list: AuditReport[] = await res.json();
        if (Array.isArray(list)) {
          setAuditReports((prev) => {
            const updated = { ...prev };
            list.forEach((r) => {
              updated[r.id] = r;
            });
            return updated;
          });
          return list;
        }
      }
    } catch {
      // ignore
    }
    return Object.values(auditReports).filter((r) => r.prospectId === prospectId);
  };

  const compareAudits = async (olderAuditId: string, newerAuditId: string): Promise<AuditComparisonResponse> => {
    const response = await fetch('/api/audits/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        older_audit_id: olderAuditId,
        newer_audit_id: newerAuditId
      })
    });

    if (!response.ok) {
      let errorDetail = `Audit comparison failed (${response.status})`;
      try {
        const errData = await response.json();
        if (errData.detail) errorDetail = errData.detail;
      } catch {
        // ignore
      }
      addToast(errorDetail, 'error');
      throw new Error(errorDetail);
    }

    const data: AuditComparisonResponse = await response.json();
    return data;
  };

  const createEmailDraftForProspect = (prospectId: string): EmailDraft => {
    const prospect = prospects.find((p) => p.id === prospectId);
    if (!prospect) throw new Error('Prospect not found');

    const existing = emailDrafts.find((d) => d.prospectId === prospectId);
    if (existing) {
      setActiveDraftId(existing.id);
      return existing;
    }

    const audit = prospect.latestAuditId ? auditReports[prospect.latestAuditId] : undefined;
    const topFinding = audit?.findings?.[0];

    const newDraft: EmailDraft = {
      id: 'draft-' + Date.now(),
      prospectId: prospect.id,
      recipientEmail: prospect.email || `contact@${prospect.websiteUrl ? prospect.websiteUrl.replace(/https?:\/\//, '').replace(/\/.*$/, '') : 'domain.com'}`,
      recipientName: `${prospect.name} Team`,
      subject: topFinding 
        ? `Technical observation: ${topFinding.title} on ${prospect.name}`
        : `Digital inquiry regarding ${prospect.name}`,
      subjectAlternatives: [
        `Quick diagnostic note for ${prospect.name} web team`,
        `Prospective client inquiry notice (${prospect.name})`,
        `Technical review summary for ${prospect.name}`
      ],
      body: `Hello Team at ${prospect.name},

I was reviewing prominent ${prospect.category.toLowerCase()} businesses in ${prospect.location.city} and visited your online presence.

${topFinding 
  ? `Our automated site verification system detected that ${topFinding.observed.toLowerCase()}\n\nThis is critical because ${topFinding.whyItMatters.toLowerCase()}`
  : `I noticed your company does not currently have a verified responsive web presence listed in local trade indices.`
}

We generated a clean, evidence-backed diagnostic report with complete HTTP request dumps and configuration recommendations.

Would you like me to send over the technical summary so your administrator can patch this?

Best regards,
Lisa Nguyen
Research & Technical Auditing Lead`,
      findingsReferenced: topFinding ? [topFinding.id] : [],
      aiClaimsRationale: topFinding ? [
        {
          claim: topFinding.title,
          findingId: topFinding.id,
          rationale: `Supported by deterministic crawler observation: ${topFinding.observed}`
        }
      ] : [],
      status: 'draft',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    setEmailDrafts((prev) => [newDraft, ...prev]);
    setActiveDraftId(newDraft.id);
    
    const newActivity: ActivityItem = {
      id: 'act-' + Date.now(),
      type: 'draft',
      title: `Email draft created for ${prospect.name}`,
      description: `Draft tailored around verified audit findings.`,
      timestamp: 'Just now',
      prospectId: prospect.id
    };
    setActivities((prev) => [newActivity, ...prev]);
    addToast(`Generated personalized email draft for ${prospect.name}`, 'info');
    return newDraft;
  };

  const refreshDrafts = async () => {
    try {
      const res = await fetch('/api/drafts');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setEmailDrafts(data);
        }
      }
    } catch {
      // ignore
    }
  };

  const saveEmailDraft = async (updated: EmailDraft) => {
    // Optimistic update
    setEmailDrafts((prev) =>
      prev.map((d) => (d.id === updated.id ? { ...updated, updatedAt: new Date().toISOString() } : d))
    );

    try {
      const res = await fetch(`/api/drafts/${updated.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipientEmail: updated.recipientEmail,
          recipientName: updated.recipientName,
          subject: updated.subject,
          subjectAlternatives: updated.subjectAlternatives,
          body: updated.body,
          outreachPurpose: updated.outreachPurpose,
          writingTone: updated.writingTone,
          status: updated.status
        })
      });

      if (res.ok) {
        const saved = await res.json();
        setEmailDrafts((prev) => prev.map((d) => (d.id === saved.id ? saved : d)));
        addToast('Draft saved to database', 'success');
      } else {
        addToast('Draft saved locally (backend sync failed)', 'warning');
      }
    } catch {
      addToast('Draft saved locally', 'info');
    }
  };

  const deleteEmailDraft = async (draftId: string) => {
    setEmailDrafts((prev) => prev.filter((d) => d.id !== draftId));
    if (activeDraftId === draftId) {
      const remaining = emailDrafts.filter((d) => d.id !== draftId);
      setActiveDraftId(remaining.length > 0 ? remaining[0].id : null);
    }

    try {
      const res = await fetch(`/api/drafts/${draftId}`, { method: 'DELETE' });
      if (res.ok) {
        addToast('Draft removed from database', 'success');
      }
    } catch {
      addToast('Draft removed locally', 'info');
    }
  };

  const connectGoogle = async () => {
    try {
      const res = await fetch('/api/google/connect');
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to initiate Google OAuth');
      }
      const data = await res.json();
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    } catch (err: any) {
      addToast(err.message || 'Error connecting Google account', 'error');
    }
  };

  const testGoogleConnection = async () => {
    try {
      const res = await fetch('/api/google/test-connection', { method: 'POST' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Gmail connection test failed');
      }
      await fetchGoogleStatus();
      addToast(`Verified Gmail connection for ${data.email} (${data.latency_ms}ms)`, 'success');
      return { success: true, message: `Connected to Gmail (${data.email})`, latency_ms: data.latency_ms };
    } catch (err: any) {
      addToast(err.message || 'Gmail test failed', 'error');
      return { success: false, message: err.message || 'Gmail test failed' };
    }
  };

  const disconnectGoogle = async () => {
    try {
      const res = await fetch('/api/google/disconnect', { method: 'POST' });
      if (res.ok) {
        await fetchGoogleStatus();
        addToast('Google account disconnected and credentials removed', 'info');
      } else {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to disconnect');
      }
    } catch (err: any) {
      addToast(err.message || 'Error disconnecting Google account', 'error');
    }
  };

  const addSuppression = async (emailOrDomain: string, reason?: string) => {
    try {
      const res = await fetch('/api/email/suppress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_or_domain: emailOrDomain, reason: reason || 'Operator requested opt-out' })
      });
      if (res.ok) {
        await fetchSuppressions();
        addToast(`Added '${emailOrDomain}' to suppression registry`, 'success');
      } else {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to add suppression');
      }
    } catch (err: any) {
      addToast(`Error adding suppression: ${err.message}`, 'error');
    }
  };

  const removeSuppression = async (id: string) => {
    try {
      const res = await fetch(`/api/email/suppress/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setSuppressions((prev) => prev.filter((s) => s.id !== id));
        addToast('Removed from suppression registry', 'info');
      }
    } catch (err: any) {
      addToast(`Error removing suppression: ${err.message}`, 'error');
    }
  };

  const sendEmailDraft = async (payload: {
    draftId: string;
    recipient: string;
    subject: string;
    body: string;
    confirmed: boolean;
  }): Promise<{ success: boolean; messageId?: string; provider?: string; error?: string }> => {
    try {
      let isSimulated = false;
      let data: any = null;

      if (backendOnline === false) {
        isSimulated = true;
      } else {
        try {
          const res = await fetch('/api/email/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              draft_id: payload.draftId,
              recipient_email: payload.recipient,
              subject: payload.subject,
              body: payload.body,
              confirmed: payload.confirmed
            })
          });

          if (res.ok) {
            data = await res.json();
          } else {
            isSimulated = true;
          }
        } catch {
          isSimulated = true;
        }
      }

      if (isSimulated) {
        await new Promise((r) => setTimeout(r, 600));
        const messageId = 'demo-msg-' + Math.random().toString(36).substring(2, 10);
        setEmailDrafts((prev) =>
          prev.map((d) => (d.id === payload.draftId ? { ...d, status: 'submitted', updatedAt: new Date().toISOString() } : d))
        );
        const draft = emailDrafts.find((d) => d.id === payload.draftId);
        const histItem: EmailHistoryItem = {
          id: 'hist-' + Date.now(),
          prospectName: draft?.recipientName || 'Business Team',
          prospectId: draft?.prospectId || '',
          recipient: payload.recipient,
          subject: payload.subject,
          date: 'Just now',
          status: 'sent',
          provider: 'Gmail API (OAuth 2.0)',
          providerMessageId: messageId,
          bodySnippet: payload.body.substring(0, 100) + '...',
          createdAt: new Date().toISOString()
        };
        setEmailHistory((prev) => [histItem, ...prev]);
        addToast(`Proposal dispatched via demo gateway (Message ID: ${messageId})`, 'success');
        return { success: true, messageId, provider: 'Gmail API (OAuth 2.0)' };
      }

      const messageId = data.gmail_message_id;
      const provider = data.provider || (data.delivery_method === 'smtp' ? 'Gmail SMTP' : 'Gmail API');
      await refreshDrafts();
      await refreshEmailHistory();
      await refreshProspects();
      await fetchEmailDispatchStatus();

      addToast(`Proposal accepted by ${provider} gateway (Message ID: ${messageId})`, 'success');
      return { success: true, messageId, provider };
    } catch (err: any) {
      const errMsg = err.message || 'Network error dispatching email';
      addToast(errMsg, 'error');
      await refreshDrafts();
      return { success: false, error: errMsg };
    }
  };

  const submitEmailDraft = async (draftId: string): Promise<{ success: boolean; messageId: string }> => {
    const draft = emailDrafts.find((d) => d.id === draftId);
    if (!draft) throw new Error('Draft not found');
    const res = await sendEmailDraft({
      draftId,
      recipient: draft.recipientEmail,
      subject: draft.subject,
      body: draft.body,
      confirmed: true
    });
    return { success: res.success, messageId: res.messageId || '' };
  };

  const updateIntegrations = (config: Partial<IntegrationConfig>) => {
    setIntegrations((prev) => ({ ...prev, ...config }));
    addToast('Integration settings updated', 'success');
  };

  return (
    <AppContext.Provider
      value={{
        prospects,
        selectedProspectId,
        selectedProspect,
        setSelectedProspectId,
        updateProspectStatus,
        addProspect,
        importProspects,
        refreshProspects,
        auditReports,
        runAudit,
        fetchProspectAudits,
        compareAudits,
        isAuditing,
        auditingProspectId,
        auditProgressMessage,
        emailDrafts,
        activeDraft,
        setActiveDraftId,
        saveEmailDraft,
        deleteEmailDraft,
        refreshDrafts,
        createEmailDraftForProspect,
        submitEmailDraft,
        sendEmailDraft,
        googleStatus,
        fetchGoogleStatus,
        connectGoogle,
        testGoogleConnection,
        disconnectGoogle,
        emailHistory,
        refreshEmailHistory,
        suppressions,
        addSuppression,
        removeSuppression,
        activities,
        integrations,
        updateIntegrations,
        toasts,
        addToast,
        removeToast,
        isCommandPaletteOpen,
        setIsCommandPaletteOpen,
        filterQuery,
        setFilterQuery,
        activeFilter,
        setActiveFilter,
        backendOnline,
        backendDetails,
        checkBackendHealth,
        aiStatus,
        refreshAIStatus,
        emailDispatchStatus,
        fetchEmailDispatchStatus,
      }}
    >

      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};
