import { 
  Prospect, 
  AuditReport, 
  EmailDraft, 
  EmailHistoryItem, 
  ActivityItem, 
  IntegrationConfig 
} from '../types';

export const INITIAL_PROSPECTS: Prospect[] = [
  {
    id: 'demo-p1',
    name: 'Apex Precision Diagnostics',
    category: 'Biotechnology & Medical Labs',
    location: {
      city: 'San Francisco',
      state: 'CA',
      country: 'United States'
    },
    websiteUrl: 'https://apexprecisiontech.com',
    websiteStatus: 'ssl_expired',
    opportunityScore: 94,
    scoreBreakdown: {
      technicalUrgency: 98,
      commercialIntent: 92,
      resolutionEase: 90
    },
    status: 'needs_review',
    lastActivity: '12m ago',
    phone: '+1 (415) 890-2341',
    email: 'contact@apexprecisiontech.com',
    auditCount: 2,
    latestAuditId: 'demo-audit-1',
    tags: ['Critical SSL', 'Medical Lab', 'High Value', 'DMARC Missing'],
    recommendedAction: 'Send technical remediation pitch focusing on impending browser SSL block and patient data trust.',
    notes: 'Primary SSL cert expires in 3 days; Let\'s Encrypt auto-renewal pipeline failed on NGINX config syntax.',
    sourceProvider: 'OpenStreetMap Overpass + Local Registry',
    discoveredAt: '2026-10-18T10:14:00Z',
    scoring: {
      opportunityScore: 94,
      scoreVersion: '2.4.0',
      confidenceScore: 0.96,
      priorityLabel: 'High',
      contactReadiness: 'verified',
      auditStatus: 'completed',
      auditAgeDays: 0,
      auditTimestamp: '2026-10-20T08:30:00Z',
      severitySummary: { high: 2, medium: 3, low: 1, info: 2 },
      factors: [
        {
          key: 'ssl_expired',
          label: 'SSL / TLS Certificate Expiry Urgency',
          contribution: 38,
          maxContribution: 40,
          status: 'FAIL',
          nature: 'confirmed_deficiency',
          summary: 'Primary certificate valid for < 72 hours with no automated ACME renewal detected.',
          evidence: [
            {
              title: 'TLS Certificate Expiry Imminent',
              severity: 'high',
              contribution: 38,
              observed: 'Certificate expires in 3 days (Issuer: DigiCert Inc). Intermediate CA bundle missing.'
            }
          ]
        },
        {
          key: 'dmarc_spf',
          label: 'Email Deliverability & Spoofing Protection',
          contribution: 28,
          maxContribution: 30,
          status: 'WARNING',
          nature: 'confirmed_deficiency',
          summary: 'Missing DMARC policy record; SPF set to softfail (~all) allowing domain impersonation.',
          evidence: [
            {
              title: 'DMARC Quarantine Policy Missing',
              severity: 'high',
              contribution: 28,
              observed: 'v=DMARC1 record absent from DNS zone.'
            }
          ]
        },
        {
          key: 'performance_ttfb',
          label: 'Core Web Vitals & TTFB Latency',
          contribution: 18,
          maxContribution: 20,
          status: 'WARNING',
          nature: 'potential_opportunity',
          summary: 'Server TTFB measured at 1,420ms due to uncompressed database queries.',
          evidence: [
            {
              title: 'Unusually Slow Server Response Time',
              severity: 'medium',
              contribution: 18,
              observed: 'TTFB: 1,420ms (Threshold: 400ms).'
            }
          ]
        }
      ],
      limitations: [],
      recommendedActions: [
        'Dispatch emergency SSL cert rotation proposal',
        'Recommend Cloudflare DNS proxying for automated edge SSL and DMARC enforcement'
      ]
    }
  },
  {
    id: 'demo-p2',
    name: 'Solaria Renewable Systems',
    category: 'Clean Energy & Solar Engineering',
    location: {
      city: 'Austin',
      state: 'TX',
      country: 'United States'
    },
    websiteUrl: 'https://solaria-renewables.io',
    websiteStatus: 'broken_pages',
    opportunityScore: 88,
    scoreBreakdown: {
      technicalUrgency: 85,
      commercialIntent: 90,
      resolutionEase: 88
    },
    status: 'draft_ready',
    lastActivity: '45m ago',
    phone: '+1 (512) 774-9021',
    email: 'hello@solaria-renewables.io',
    auditCount: 1,
    latestAuditId: 'demo-audit-2',
    tags: ['Mobile Viewport Missing', 'Broken Canonical', 'Solar Tech'],
    recommendedAction: 'Propose responsive layout fix; mobile quote calculator fails to load on iOS Safari.',
    notes: 'High commercial intent with active Google Ads campaign, yet mobile landing page drops 60% of traffic.',
    sourceProvider: 'OpenStreetMap Overpass',
    discoveredAt: '2026-10-18T14:22:00Z',
    scoring: {
      opportunityScore: 88,
      scoreVersion: '2.4.0',
      confidenceScore: 0.94,
      priorityLabel: 'High',
      contactReadiness: 'verified',
      auditStatus: 'completed',
      auditAgeDays: 1,
      auditTimestamp: '2026-10-19T11:15:00Z',
      severitySummary: { high: 1, medium: 4, low: 2, info: 1 },
      factors: [
        {
          key: 'viewport_missing',
          label: 'Mobile Viewport Meta Absence',
          contribution: 32,
          maxContribution: 35,
          status: 'FAIL',
          nature: 'confirmed_deficiency',
          summary: '<meta name="viewport"> tag missing in <head>, causing desktop layout squeeze on mobile.',
          evidence: [
            {
              title: 'Mobile Viewport Missing',
              severity: 'high',
              contribution: 32,
              observed: 'No viewport meta tag declared in DOM.'
            }
          ]
        }
      ],
      limitations: [],
      recommendedActions: [
        'Propose 48-hour mobile conversion redesign',
        'Fix canonical URL loops hurting regional organic search ranking'
      ]
    }
  },
  {
    id: 'demo-p3',
    name: 'Vanguard Legal Partners LLP',
    category: 'Corporate & Intellectual Property Law',
    location: {
      city: 'Chicago',
      state: 'IL',
      country: 'United States'
    },
    websiteUrl: 'https://vanguardlawgroup.com',
    websiteStatus: 'verified_accessible',
    opportunityScore: 82,
    scoreBreakdown: {
      technicalUrgency: 80,
      commercialIntent: 84,
      resolutionEase: 82
    },
    status: 'needs_review',
    lastActivity: '2h ago',
    phone: '+1 (312) 640-1120',
    email: 'partners@vanguardlawgroup.com',
    auditCount: 1,
    latestAuditId: 'demo-audit-3',
    tags: ['TLS 1.0 Enabled', 'Cloudflare XOR Decoded', 'High Retainer'],
    recommendedAction: 'Pitch TLS hardening & modern client intake portal compliance.',
    notes: 'Email was obfuscated behind Cloudflare data-cfemail; successfully decoded via client XOR engine.',
    sourceProvider: 'Local Commercial Directory',
    discoveredAt: '2026-10-19T08:00:00Z'
  },
  {
    id: 'demo-p4',
    name: 'Bakehouse Artisan Roasters',
    category: 'Specialty Food & Hospitality',
    location: {
      city: 'Portland',
      state: 'OR',
      country: 'United States'
    },
    websiteUrl: 'https://bakehousepdx.coffee',
    websiteStatus: 'verified_accessible',
    opportunityScore: 78,
    scoreBreakdown: {
      technicalUrgency: 74,
      commercialIntent: 82,
      resolutionEase: 80
    },
    status: 'new',
    lastActivity: '3h ago',
    phone: '+1 (503) 912-3840',
    email: 'orders@bakehousepdx.coffee',
    auditCount: 1,
    latestAuditId: 'demo-audit-4',
    tags: ['Slow TTFB', 'Unminified CSS', 'Local Brand'],
    recommendedAction: 'Offer WooCommerce speed optimization and mobile ordering overhaul.'
  },
  {
    id: 'demo-p5',
    name: 'Novus Cloud Infrastructure',
    category: 'Managed IT & Enterprise Networks',
    location: {
      city: 'Denver',
      state: 'CO',
      country: 'United States'
    },
    websiteUrl: 'https://novuscloudops.net',
    websiteStatus: 'dns_error',
    opportunityScore: 74,
    scoreBreakdown: {
      technicalUrgency: 78,
      commercialIntent: 70,
      resolutionEase: 75
    },
    status: 'needs_audit',
    lastActivity: '5h ago',
    phone: '+1 (720) 441-9988',
    email: 'admin@novuscloudops.net',
    auditCount: 0,
    tags: ['DNS Zone Drift', 'Enterprise IT'],
    recommendedAction: 'Run full DNS zone diagnostic and propose secondary authoritative nameserver mesh.'
  },
  {
    id: 'demo-p6',
    name: 'Zenith Orthodontic Specialists',
    category: 'Healthcare & Dental Practices',
    location: {
      city: 'Miami',
      state: 'FL',
      country: 'United States'
    },
    websiteUrl: 'https://zenithorthomiami.com',
    websiteStatus: 'verified_accessible',
    opportunityScore: 68,
    scoreBreakdown: {
      technicalUrgency: 62,
      commercialIntent: 74,
      resolutionEase: 70
    },
    status: 'contacted',
    lastActivity: '1d ago',
    phone: '+1 (305) 552-4411',
    email: 'appointments@zenithorthomiami.com',
    auditCount: 2,
    tags: ['Contacted', 'Single-Send Confirmed', 'Patient Portal'],
    recommendedAction: 'Follow up in 4 days regarding HIPAA contact form encryption report.'
  },
  {
    id: 'demo-p7',
    name: 'Nexus Freight & Logistics',
    category: 'Supply Chain & Heavy Transport',
    location: {
      city: 'Seattle',
      state: 'WA',
      country: 'United States'
    },
    websiteUrl: 'https://nexusfreightpacific.com',
    websiteStatus: 'verified_accessible',
    opportunityScore: 62,
    scoreBreakdown: {
      technicalUrgency: 58,
      commercialIntent: 68,
      resolutionEase: 60
    },
    status: 'new',
    lastActivity: '1d ago',
    phone: '+1 (206) 880-1290',
    email: 'dispatch@nexusfreightpacific.com',
    auditCount: 1,
    tags: ['B2B Logistics', 'Missing SPF'],
    recommendedAction: 'Demonstrate email spoofing risk with unauthenticated SPF records.'
  },
  {
    id: 'demo-p8',
    name: 'Crestview Architecture Studio',
    category: 'Commercial Architecture & Urban Design',
    location: {
      city: 'Boston',
      state: 'MA',
      country: 'United States'
    },
    websiteUrl: 'https://crestview-arch.design',
    websiteStatus: 'verified_accessible',
    opportunityScore: 48,
    scoreBreakdown: {
      technicalUrgency: 42,
      commercialIntent: 52,
      resolutionEase: 50
    },
    status: 'archived',
    lastActivity: '3d ago',
    phone: '+1 (617) 229-4501',
    email: 'studio@crestview-arch.design',
    auditCount: 1,
    tags: ['Low Priority', 'Portfolio Clean'],
    recommendedAction: 'Monitor quarterly for SSL rotation cycle.'
  }
];

export const MOCK_AUDIT_REPORTS: Record<string, AuditReport> = {
  'demo-audit-1': {
    id: 'demo-audit-1',
    prospectId: 'demo-p1',
    url: 'https://apexprecisiontech.com',
    timestamp: '2026-10-20T08:30:00Z',
    status: 'completed',
    overallScore: 38,
    findings: [
      {
        id: 'f-ssl-exp',
        prospectId: 'demo-p1',
        title: 'TLS/SSL Certificate Expiring in Under 72 Hours',
        severity: 'high',
        observed: 'Certificate issuer DigiCert Inc, valid until Oct 23, 2026. Automated ACME challenge failing with 403 on .well-known/acme-challenge.',
        evidence: 'Subject: CN=apexprecisiontech.com | NotAfter: 2026-10-23T11:59:00Z | Error: OCSP Stapling Disabled',
        whyItMatters: 'Major browsers (Chrome, Safari, Edge) will immediately display red full-screen interstitial warning "Your connection is not private", dropping 90%+ patient intake submissions.',
        recommendedAction: 'Update NGINX reverse proxy location block to allow ACME challenge traffic or install zero-downtime Cloudflare Universal SSL.',
        confidence: 0.99,
        category: 'security'
      },
      {
        id: 'f-dmarc-missing',
        prospectId: 'demo-p1',
        title: 'Missing DMARC Enforcement Policy Record',
        severity: 'high',
        observed: 'DNS lookup for _dmarc.apexprecisiontech.com returned NXDOMAIN.',
        evidence: 'dig TXT _dmarc.apexprecisiontech.com -> NXDOMAIN (No Record)',
        whyItMatters: 'Anyone can forge emails claiming to be billing@apexprecisiontech.com or results@apexprecisiontech.com, failing Gmail/Yahoo 2024+ sender authentication mandates.',
        recommendedAction: 'Publish TXT record _dmarc.apexprecisiontech.com with policy "v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@apexprecisiontech.com".',
        confidence: 0.98,
        category: 'security'
      },
      {
        id: 'f-slow-ttfb',
        prospectId: 'demo-p1',
        title: 'Unusually High Time-to-First-Byte (1,420ms)',
        severity: 'medium',
        observed: 'Initial HTML handshake takes 1.42s before the browser receives the first byte.',
        evidence: 'curl -w "TTFB: %{time_starttransfer}s" -> 1.421s across 3 consecutive probes.',
        whyItMatters: 'Google Search algorithm penalizes pages with TTFB > 600ms, pushing lab service landing pages below local competitors.',
        recommendedAction: 'Enable Redis page caching and upgrade PHP-FPM / database query pooling.',
        confidence: 0.92,
        category: 'performance'
      },
      {
        id: 'f-missing-hsts',
        prospectId: 'demo-p1',
        title: 'Strict-Transport-Security (HSTS) Header Absent',
        severity: 'medium',
        observed: 'HTTP responses lack the Strict-Transport-Security header.',
        evidence: 'Header inspection: Strict-Transport-Security header null.',
        whyItMatters: 'Leaves users vulnerable to SSL stripping attacks on public Wi-Fi networks.',
        recommendedAction: 'Add "Strict-Transport-Security: max-age=31536000; includeSubDomains; preload" in web server response headers.',
        confidence: 0.95,
        category: 'security'
      }
    ],
    rawDns: {
      aRecord: '198.51.100.42',
      mxRecord: 'mail.apexprecisiontech.com (Priority 10)',
      responseMs: 44,
      nameservers: ['ns1.dnsimple.com', 'ns2.dnsimple.com']
    },
    rawSsl: {
      valid: true,
      issuer: 'DigiCert Global Root CA',
      expiresDays: 3,
      tlsVersion: 'TLS 1.3',
      cipher: 'TLS_AES_256_GCM_SHA384'
    },
    performance: {
      ttfbMs: 1420,
      domReadyMs: 2840,
      pageSizeKb: 4120,
      mobileViewportPresent: true
    },
    headers: {
      'server': 'nginx/1.22.1',
      'content-type': 'text/html; charset=UTF-8',
      'x-powered-by': 'PHP/8.1.18',
      'connection': 'keep-alive'
    }
  },
  'demo-audit-2': {
    id: 'demo-audit-2',
    prospectId: 'demo-p2',
    url: 'https://solaria-renewables.io',
    timestamp: '2026-10-19T11:15:00Z',
    status: 'completed',
    overallScore: 54,
    findings: [
      {
        id: 'f-viewport-missing',
        prospectId: 'demo-p2',
        title: 'Mobile Viewport Meta Tag Missing in DOM',
        severity: 'high',
        observed: 'No <meta name="viewport"> tag declared in document head.',
        evidence: 'HTML head inspection: missing viewport attribute.',
        whyItMatters: 'Mobile browsers default to 980px desktop scaling, rendering tiny text and breaking interactive quote forms on smartphones.',
        recommendedAction: 'Inject <meta name="viewport" content="width=device-width, initial-scale=1.0"> into document <head>.',
        confidence: 1.0,
        category: 'reachability'
      },
      {
        id: 'f-mixed-content',
        prospectId: 'demo-p2',
        title: 'Passive Mixed Content Detected (HTTP images on HTTPS)',
        severity: 'medium',
        observed: '14 solar panel diagram images loaded over unencrypted http:// urls.',
        evidence: '<img src="http://solaria-renewables.io/assets/panel-spec.jpg">',
        whyItMatters: 'Causes browser warning icon and prevents browser cache sharing.',
        recommendedAction: 'Rewrite internal asset links to protocol-relative (//) or HTTPS.',
        confidence: 0.94,
        category: 'security'
      }
    ],
    rawDns: {
      aRecord: '203.0.113.88',
      mxRecord: 'aspmx.l.google.com (Priority 1)',
      responseMs: 62,
      nameservers: ['ns1.he.net', 'ns2.he.net']
    },
    rawSsl: {
      valid: true,
      issuer: "Let's Encrypt Authority X3",
      expiresDays: 48,
      tlsVersion: 'TLS 1.2',
      cipher: 'ECDHE-RSA-AES128-GCM-SHA256'
    },
    performance: {
      ttfbMs: 380,
      domReadyMs: 1980,
      pageSizeKb: 2850,
      mobileViewportPresent: false
    },
    headers: {
      'server': 'Apache/2.4.52 (Ubuntu)',
      'content-type': 'text/html; charset=UTF-8'
    }
  }
};

export const INITIAL_EMAIL_DRAFTS: EmailDraft[] = [
  {
    id: 'demo-draft-1',
    prospectId: 'demo-p1',
    auditId: 'demo-audit-1',
    recipientEmail: 'contact@apexprecisiontech.com',
    recipientName: 'Dr. Harrison',
    subject: 'Urgent: Impending SSL certificate disruption on apexprecisiontech.com',
    subjectAlternatives: [
      'Quick technical alert regarding apexprecisiontech.com security warning',
      'Action needed: SSL expiry on patient intake form (apexprecisiontech.com)'
    ],
    body: `Hi Dr. Harrison,

I noticed during an infrastructure diagnostic of apexprecisiontech.com that your primary TLS/SSL security certificate is scheduled to expire in under 72 hours (Oct 23, 2026).

Currently, your web server's ACME automated renewal is returning a 403 Forbidden error on the .well-known/acme-challenge directory. Once expired, Chrome and Safari will display full-screen warning interstitials ("Your connection is not private") to prospective patients trying to access your intake forms.

Additionally, your DNS zone lacks a DMARC policy record (_dmarc.apexprecisiontech.com), meaning emails sent from your domain are at risk of being quarantined by Google and Yahoo recipient inboxes.

We specialize in rapid zero-downtime certificate rotation and DNS hardening for healthcare organizations. Would you have 10 minutes tomorrow afternoon to review the remediation steps?

Best regards,
Prajwal & The Leddro Technical Team`,
    status: 'draft',
    createdAt: '2026-10-20T08:45:00Z',
    updatedAt: '2026-10-20T08:50:00Z',
    findingsReferenced: ['f-ssl-exp', 'f-dmarc-missing'],
    aiClaimsRationale: [
      {
        claim: 'primary TLS/SSL security certificate is scheduled to expire in under 72 hours (Oct 23, 2026)',
        findingId: 'f-ssl-exp',
        rationale: 'Verified from DigiCert TLS NotAfter probe.',
        evidenceType: 'TLS Handshake Probe'
      },
      {
        claim: 'DNS zone lacks a DMARC policy record (_dmarc.apexprecisiontech.com)',
        findingId: 'f-dmarc-missing',
        rationale: 'Verified from DNS TXT lookup returning NXDOMAIN.',
        evidenceType: 'DNS Zone Query'
      }
    ]
  }
];

export const INITIAL_EMAIL_HISTORY: EmailHistoryItem[] = [
  {
    id: 'demo-hist-1',
    prospectId: 'demo-p6',
    recipient: 'appointments@zenithorthomiami.com',
    prospectName: 'Zenith Orthodontic Specialists',
    subject: 'Security observation regarding patient contact forms on zenithorthomiami.com',
    bodySnippet: 'Hi Zenith Orthodontics team, our diagnostics flagged an unencrypted HTTP submission endpoint...',
    date: '2026-10-19T14:30:00Z',
    status: 'sent',
    provider: 'Gmail API (OAuth 2.0)'
  }
];

export const INITIAL_ACTIVITIES: ActivityItem[] = [
  {
    id: 'act-1',
    timestamp: 'Just now',
    type: 'draft',
    title: 'Evidence-backed outreach draft synthesized',
    description: 'Generated technical remediation proposal for Apex Precision Diagnostics (Score: 94)',
    prospectId: 'demo-p1'
  },
  {
    id: 'act-2',
    timestamp: '25m ago',
    type: 'audit',
    title: 'Automated diagnostic scan completed',
    description: 'Inspected apexprecisiontech.com: Discovered 4 vulnerabilities (Score: 38/100)',
    prospectId: 'demo-p1'
  },
  {
    id: 'act-3',
    timestamp: '1h ago',
    type: 'import',
    title: 'Regional prospect batch ingested',
    description: 'Loaded 8 verified commercial targets from OpenStreetMap Overpass',
    prospectId: 'demo-p2'
  }
];

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
    provider: 'gemini',
    isConfigured: true,
    model: 'gemini-1.5-flash',
    status: 'ready'
  },
  discoveryProvider: {
    provider: 'osm_overpass',
    isConfigured: true,
    activeName: 'OpenStreetMap Overpass + Local Registry Index',
    rateLimitRemaining: 9400
  }
};
