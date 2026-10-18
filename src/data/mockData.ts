import { Prospect, AuditReport, EmailDraft, EmailHistoryItem, ActivityItem, IntegrationConfig } from '../types';

export const INITIAL_PROSPECTS: Prospect[] = [
  {
    id: 'pr-1',
    name: 'Northstar Interiors',
    category: 'Interior design',
    location: {
      city: 'Navi Mumbai',
      state: 'Maharashtra',
      country: 'India',
    },
    websiteUrl: 'https://northstarinteriors.in',
    websiteStatus: 'broken_pages',
    opportunityScore: 82,
    scoreBreakdown: {
      technicalUrgency: 35,
      commercialIntent: 25,
      resolutionEase: 22,
    },
    status: 'needs_review',
    lastActivity: '12 mins ago',
    phone: '+91 22 2789 4412',
    email: 'contact@northstarinteriors.in',
    auditCount: 2,
    latestAuditId: 'audit-northstar-1',
    tags: ['High Value', 'Broken Contact Form', 'Navi Mumbai Hub'],
    recommendedAction: 'Send outreach proposal detailing HTTP 404 on contact portal and mobile viewport fix.',
    notes: 'Premium commercial studio with 22 team members. Primary lead capture form is currently unreachable.'
  },
  {
    id: 'pr-2',
    name: 'Harbor Furniture Works',
    category: 'Manufacturing',
    location: {
      city: 'Pune',
      state: 'Maharashtra',
      country: 'India',
    },
    websiteUrl: 'https://harborfurniture.co.in',
    websiteStatus: 'active',
    opportunityScore: 78,
    scoreBreakdown: {
      technicalUrgency: 28,
      commercialIntent: 26,
      resolutionEase: 24,
    },
    status: 'needs_review',
    lastActivity: '1 hour ago',
    phone: '+91 20 6645 8890',
    email: 'inquiries@harborfurniture.co.in',
    auditCount: 1,
    latestAuditId: 'audit-harbor-1',
    tags: ['Export Ready', 'Heavy Assets', 'Pune Industrial'],
    recommendedAction: 'Propose website speed optimization and asset compression for international buyers.',
    notes: 'B2B wooden furniture exporter. Homepage takes 3.8s to load due to 14MB uncompressed hero assets.'
  },
  {
    id: 'pr-3',
    name: 'Willow Studio',
    category: 'Architecture',
    location: {
      city: 'Bengaluru',
      state: 'Karnataka',
      country: 'India',
    },
    websiteUrl: 'https://willowstudio.design',
    websiteStatus: 'active',
    opportunityScore: 64,
    scoreBreakdown: {
      technicalUrgency: 18,
      commercialIntent: 24,
      resolutionEase: 22,
    },
    status: 'draft_ready',
    lastActivity: 'Yesterday',
    phone: '+91 80 4112 9081',
    email: 'studio@willowstudio.design',
    auditCount: 1,
    latestAuditId: 'audit-willow-1',
    tags: ['Sustainable Architecture', 'Outdated TLS'],
    recommendedAction: 'Review prepared email draft regarding TLS deprecation and OpenGraph card preview fixes.',
    notes: 'Award-winning sustainable architect practice. Insecure cipher configuration triggers corporate browser warnings.'
  },
  {
    id: 'pr-4',
    name: 'Apex Precision Tech',
    category: 'Machining & Tooling',
    location: {
      city: 'Chennai',
      state: 'Tamil Nadu',
      country: 'India',
    },
    websiteUrl: 'https://apexprecisiontech.com',
    websiteStatus: 'ssl_expired',
    opportunityScore: 91,
    scoreBreakdown: {
      technicalUrgency: 40,
      commercialIntent: 28,
      resolutionEase: 23,
    },
    status: 'needs_review',
    lastActivity: '2 days ago',
    phone: '+91 44 2490 3310',
    email: 'operations@apexprecisiontech.com',
    auditCount: 3,
    latestAuditId: 'audit-apex-1',
    tags: ['Critical SSL', 'Automotive Supplier', 'Immediate Action'],
    recommendedAction: 'Alert director regarding expired SSL certificate blocking international defense and automotive RFQs.',
    notes: 'SSL certificate expired 6 days ago. Web traffic completely blocked by Chrome and Firefox security walls.'
  },
  {
    id: 'pr-5',
    name: 'Vesta Ceramic Works',
    category: 'Home Goods',
    location: {
      city: 'Morbi',
      state: 'Gujarat',
      country: 'India',
    },
    websiteUrl: 'https://vestaceramics.biz',
    websiteStatus: 'dns_error',
    opportunityScore: 86,
    scoreBreakdown: {
      technicalUrgency: 36,
      commercialIntent: 27,
      resolutionEase: 23,
    },
    status: 'needs_audit',
    lastActivity: '3 days ago',
    phone: '+91 2822 254 119',
    email: 'sales@vestaceramics.biz',
    auditCount: 0,
    tags: ['Ceramics Hub', 'DNS Failure', 'High Revenue'],
    recommendedAction: 'Execute full crawler audit to diagnose parked domain DNS misdirection.',
    notes: 'Large tile exporter in Morbi cluster. Main domain CNAME currently resolves to parking registrar IP.'
  },
  {
    id: 'pr-6',
    name: 'Solas Dental Care',
    category: 'Healthcare',
    location: {
      city: 'Hyderabad',
      state: 'Telangana',
      country: 'India',
    },
    websiteUrl: 'https://solasdentalcare.org',
    websiteStatus: 'broken_pages',
    opportunityScore: 79,
    scoreBreakdown: {
      technicalUrgency: 32,
      commercialIntent: 25,
      resolutionEase: 22,
    },
    status: 'needs_review',
    lastActivity: '4 days ago',
    phone: '+91 40 4010 7720',
    email: 'help@solasdentalcare.org',
    auditCount: 1,
    latestAuditId: 'audit-solas-1',
    tags: ['Multi-clinic', 'HTTP 500 Booking', 'Local SEO'],
    recommendedAction: 'Send diagnostic briefing on appointment API 500 error preventing online patient registration.',
    notes: 'Premium 3-branch dental clinic. Booking page returns 500 Internal Server Error upon date selection.'
  },
  {
    id: 'pr-7',
    name: 'Kaveri Woodcrafts',
    category: 'Handicrafts & Decor',
    location: {
      city: 'Mysuru',
      state: 'Karnataka',
      country: 'India',
    },
    websiteUrl: undefined,
    websiteStatus: 'not_listed',
    opportunityScore: 88,
    scoreBreakdown: {
      technicalUrgency: 34,
      commercialIntent: 30,
      resolutionEase: 24,
    },
    status: 'new',
    lastActivity: '4 days ago',
    phone: '+91 821 241 8830',
    email: 'kaveriwoodcrafts.mys@gmail.com',
    auditCount: 0,
    tags: ['Zero Digital Presence', 'High Google Rating', 'Catalog Opportunity'],
    recommendedAction: 'Engage via phone/email proposing turnkey digital catalog and merchant storefront.',
    notes: '4.8 star rated business on Google Maps with 160+ reviews but no website registered or active.'
  },
  {
    id: 'pr-8',
    name: 'Crestline Logistics',
    category: 'Freight & Supply',
    location: {
      city: 'New Delhi',
      state: 'Delhi',
      country: 'India',
    },
    websiteUrl: 'https://crestlinelogistics.in',
    websiteStatus: 'active',
    opportunityScore: 58,
    scoreBreakdown: {
      technicalUrgency: 16,
      commercialIntent: 22,
      resolutionEase: 20,
    },
    status: 'contacted',
    lastActivity: '5 days ago',
    phone: '+91 11 4988 2300',
    email: 'dispatch@crestlinelogistics.in',
    auditCount: 1,
    latestAuditId: 'audit-crestline-1',
    tags: ['Email Deliverability', 'Cold Outreach Sent'],
    recommendedAction: 'Awaiting reply to SPF/DKIM deliverability audit sent on April 13.',
    notes: 'Corporate domain lacked SPF and DMARC records causing quotes to be flagged by Outlook Spam filters.'
  }
];

export const MOCK_AUDIT_REPORTS: Record<string, AuditReport> = {
  'audit-northstar-1': {
    id: 'audit-northstar-1',
    prospectId: 'pr-1',
    timestamp: '2026-04-18 10:42:18 UTC',
    status: 'completed',
    overallScore: 82,
    findings: [
      {
        id: 'f-ns-1',
        prospectId: 'pr-1',
        title: 'Contact page returned HTTP 404',
        severity: 'high',
        observed: 'The contact page URL (/contact-us) linked from the main navigation header returned HTTP 404 during the audit crawl.',
        evidence: `GET /contact-us HTTP/1.1\nHost: northstarinteriors.in\nUser-Agent: LeddroAuditor/2.4 (+https://leddro.io/bot)\n\nHTTP/1.1 404 Not Found\nDate: Sat, 18 Apr 2026 10:42:19 GMT\nServer: nginx/1.24.0\nContent-Type: text/html\nContent-Length: 162\nConnection: keep-alive`,
        whyItMatters: 'Visitors seeking interior design quotes or consultation cannot reach the business through this primary call-to-action, causing direct lead drop-off.',
        recommendedAction: 'Verify the web server routing configuration, check page slug consistency, and deploy a 301 redirect or restore the active contact view.',
        confidence: 0.99,
        category: 'reachability',
        httpStatus: 404,
        responseTimeMs: 142
      },
      {
        id: 'f-ns-2',
        prospectId: 'pr-1',
        title: 'Missing mobile viewport meta tag',
        severity: 'medium',
        observed: 'The HTML <head> element does not contain a standard viewport definition (<meta name="viewport" content="width=device-width, initial-scale=1">).',
        evidence: `<!-- Document Head Snippet -->\n<head>\n  <title>Northstar Interiors - Architecture &amp; Spatial Design</title>\n  <meta charset="utf-8">\n  <link rel="stylesheet" href="/assets/style.css">\n  <!-- Missing: <meta name="viewport" ...> -->\n</head>`,
        whyItMatters: 'Mobile browsers default to a 980px desktop viewport fallback, resulting in tiny unreadable text and horizontal scrolling on smartphone devices.',
        recommendedAction: 'Add the standard responsive viewport meta tag to the root template header.',
        confidence: 0.98,
        category: 'performance'
      },
      {
        id: 'f-ns-3',
        prospectId: 'pr-1',
        title: 'Uncompressed high-resolution portfolio images',
        severity: 'low',
        observed: 'Three featured hero images exceed 4.2MB each and are served in raw PNG without WebP/AVIF modern compression or srcset dimensions.',
        evidence: `GET /gallery/penthouse-living.png (4,412,890 bytes, 3840x2160 raw)\nGET /gallery/commercial-lobby.png (4,188,410 bytes, 3840x2160 raw)\nTotal Page Transfer: 12.8 MB (Recommended threshold: < 2.5 MB)`,
        whyItMatters: 'Increases initial visual paint latency to over 4.8 seconds on 4G connections, penalizing Google Core Web Vitals rankings.',
        recommendedAction: 'Convert images to WebP with 82% quality compression and implement responsive srcset widths.',
        confidence: 0.95,
        category: 'performance'
      },
      {
        id: 'f-ns-4',
        prospectId: 'pr-1',
        title: 'Missing OpenGraph metadata for social sharing',
        severity: 'info',
        observed: 'No og:title, og:image, or og:description tags found in the primary document header.',
        evidence: `og:title: [MISSING]\nog:image: [MISSING]\nog:description: [MISSING]\ntwitter:card: [MISSING]`,
        whyItMatters: 'Shared links on WhatsApp, LinkedIn, or Slack will render as bare text links without preview cards or studio imagery.',
        recommendedAction: 'Define standard OpenGraph meta tags with a 1200x630px showcase card image.',
        confidence: 0.96,
        category: 'seo_meta'
      }
    ],
    rawDns: {
      aRecord: '103.142.18.91 (Mumbai, Tata Communications DC)',
      mxRecord: 'mail.northstarinteriors.in (Priority 10)',
      responseMs: 24,
      nameservers: ['ns1.dnsindia.net', 'ns2.dnsindia.net']
    },
    rawSsl: {
      valid: true,
      issuer: "Let's Encrypt Authority R3",
      expiresDays: 44,
      tlsVersion: 'TLSv1.3',
      cipher: 'TLS_AES_256_GCM_SHA384'
    },
    performance: {
      ttfbMs: 310,
      domReadyMs: 1420,
      pageSizeKb: 13100,
      mobileViewportPresent: false
    },
    headers: {
      'server': 'nginx/1.24.0',
      'content-type': 'text/html; charset=UTF-8',
      'x-frame-options': 'SAMEORIGIN',
      'strict-transport-security': 'max-age=31536000; includeSubDomains',
      'x-content-type-options': 'nosniff'
    }
  },
  'audit-apex-1': {
    id: 'audit-apex-1',
    prospectId: 'pr-4',
    timestamp: '2026-04-16 14:10:05 UTC',
    status: 'completed',
    overallScore: 91,
    findings: [
      {
        id: 'f-ap-1',
        prospectId: 'pr-4',
        title: 'SSL Certificate expired (NET::ERR_CERT_DATE_INVALID)',
        severity: 'high',
        observed: 'The TLS certificate expired 6 days ago on April 10, 2026. Browsers reject the connection with full-screen security warnings.',
        evidence: `Certificate Serial: 03:B4:72:D1:9A:88\nValidity Not After: Fri, 10 Apr 2026 23:59:59 GMT\nCurrent Verification Time: Thu, 16 Apr 2026 14:10:05 GMT\nStatus: EXPIRED (+6 days)\nError Code: CERT_DATE_INVALID`,
        whyItMatters: 'Over 95% of corporate purchasing agents abandon visits immediately when encountering browser red warning screens.',
        recommendedAction: 'Renew the SSL certificate immediately through ACME automated bot or issuing Certificate Authority.',
        confidence: 1.0,
        category: 'security'
      },
      {
        id: 'f-ap-2',
        prospectId: 'pr-4',
        title: 'Insecure RFQ upload form transmitting over HTTP',
        severity: 'high',
        observed: 'The technical spec file upload form action targets an unencrypted http:// endpoint without transport security.',
        evidence: `<form action="http://apexprecisiontech.com/upload_spec.php" method="POST" enctype="multipart/form-data">`,
        whyItMatters: 'Proprietary CAD files and client technical specifications are sent unencrypted over plaintext channels.',
        recommendedAction: 'Enforce HTTPS for all form actions and add strict HSTS headers.',
        confidence: 0.99,
        category: 'security'
      }
    ],
    rawDns: {
      aRecord: '115.241.80.12 (Chennai, Bharti Airtel)',
      mxRecord: 'smtp.apexprecisiontech.com (Priority 10)',
      responseMs: 19,
      nameservers: ['ns1.apexprecisiontech.com', 'ns2.apexprecisiontech.com']
    },
    rawSsl: {
      valid: false,
      issuer: 'Sectigo RSA Domain Validation CA',
      expiresDays: -6,
      tlsVersion: 'TLSv1.2',
      cipher: 'ECDHE-RSA-AES256-GCM-SHA384'
    },
    performance: {
      ttfbMs: 640,
      domReadyMs: 2200,
      pageSizeKb: 4200,
      mobileViewportPresent: true
    },
    headers: {
      'server': 'Apache/2.4.52 (Ubuntu)',
      'content-type': 'text/html; charset=UTF-8'
    }
  }
};

export const INITIAL_EMAIL_DRAFTS: EmailDraft[] = [
  {
    id: 'draft-1',
    prospectId: 'pr-1',
    recipientEmail: 'contact@northstarinteriors.in',
    recipientName: 'Northstar Interiors Management',
    subject: 'Quick heads up regarding broken contact page on northstarinteriors.in',
    subjectAlternatives: [
      'Issue detected on northstarinteriors.in contact form (HTTP 404)',
      'Potential client inquiries failing on northstarinteriors.in',
      'Technical observation: Broken inquiry URL on Northstar Interiors'
    ],
    body: `Hello Team Northstar,

I was reviewing prominent interior design studios in Navi Mumbai and visited your website (northstarinteriors.in).

I noticed that your primary contact page link (https://northstarinteriors.in/contact-us) currently returns an HTTP 404 Not Found error. 

Because this is the direct link prospective clients click to request consultations or project scopes, any new inquiries are likely bouncing before reaching your team. Additionally, the site currently lacks a mobile viewport tag, causing the portfolio to render at desktop resolution on phones.

We compiled a deterministic diagnostic report showing the exact server response codes and evidence.

Would you like me to send over the technical summary so your web administrator can patch the routing?

Best regards,
Lisa Nguyen
Research & Technical Auditing Lead`,
    findingsReferenced: ['f-ns-1', 'f-ns-2'],
    aiClaimsRationale: [
      {
        claim: 'Contact page link returns an HTTP 404 Not Found error',
        findingId: 'f-ns-1',
        rationale: 'Deterministic crawler received HTTP/1.1 404 on /contact-us at 10:42:19 GMT.'
      },
      {
        claim: 'Lacks a mobile viewport tag causing desktop rendering on phones',
        findingId: 'f-ns-2',
        rationale: 'HTML head inspection verified the absence of <meta name="viewport">.'
      }
    ],
    status: 'draft',
    createdAt: '2026-04-18 11:05:00 UTC',
    updatedAt: '2026-04-18 11:30:14 UTC'
  },
  {
    id: 'draft-2',
    prospectId: 'pr-3',
    recipientEmail: 'studio@willowstudio.design',
    recipientName: 'Willow Studio Team',
    subject: 'Technical note regarding TLS legacy ciphers on willowstudio.design',
    subjectAlternatives: [
      'Browser warning check on willowstudio.design',
      'Security observation for Willow Studio web infrastructure'
    ],
    body: `Hi Team at Willow Studio,

While reviewing your architectural portfolio online, our automated security scanner flagged that your web server is still negotiating deprecated TLS 1.0/1.1 protocols and is missing social preview OpenGraph cards.

Modern enterprise networks and updated Chrome browsers are increasingly blocking sites with legacy cipher suites.

Happy to share our verified audit report if helpful to your developers.

Warm regards,
Lisa Nguyen`,
    findingsReferenced: [],
    aiClaimsRationale: [
      {
        claim: 'Server is still negotiating deprecated TLS 1.0/1.1',
        findingId: 'tls-cipher',
        rationale: 'SSL handshake verified legacy cipher suite acceptance.'
      }
    ],
    status: 'awaiting_approval',
    createdAt: '2026-04-17 15:20:00 UTC',
    updatedAt: '2026-04-17 16:10:00 UTC'
  }
];

export const INITIAL_EMAIL_HISTORY: EmailHistoryItem[] = [
  {
    id: 'hist-1',
    recipient: 'dispatch@crestlinelogistics.in',
    prospectName: 'Crestline Logistics',
    prospectId: 'pr-8',
    subject: 'Email deliverability notice regarding crestlinelogistics.in DNS records',
    date: '2026-04-13 14:15 UTC',
    status: 'submitted',
    provider: 'Gmail API (OAuth 2.0)',
    providerMessageId: 'msg_18ec9930f7810aa2',
    bodySnippet: 'Noticed your domain lacks valid SPF and DMARC records, which causes quote emails to land in corporate junk folders...'
  },
  {
    id: 'hist-2',
    recipient: 'operations@apexprecisiontech.com',
    prospectName: 'Apex Precision Tech',
    prospectId: 'pr-4',
    subject: 'Urgent: Expired SSL Certificate on apexprecisiontech.com',
    date: '2026-04-16 09:30 UTC',
    status: 'submitted',
    provider: 'Gmail API (OAuth 2.0)',
    providerMessageId: 'msg_18ed5a2108849bca',
    bodySnippet: 'Your security certificate expired on April 10, resulting in browser warning screens for all visitors...'
  },
  {
    id: 'hist-3',
    recipient: 'info@zenithaerospace.in',
    prospectName: 'Zenith Aerospace Components',
    prospectId: 'pr-archive-1',
    subject: 'Technical verification report for zenithaerospace.in',
    date: '2026-04-10 11:00 UTC',
    status: 'failed',
    provider: 'Direct SMTP',
    providerMessageId: 'err_smtp_550_mailbox_unavailable',
    bodySnippet: 'SMTP server returned 550 Mailbox does not exist. Re-routing to secondary contact address.'
  }
];

export const INITIAL_ACTIVITIES: ActivityItem[] = [
  {
    id: 'act-1',
    type: 'audit',
    title: 'Audit completed for Northstar Interiors',
    description: 'Found 4 technical issues including high-severity HTTP 404 on /contact-us.',
    timestamp: '12 mins ago',
    prospectId: 'pr-1'
  },
  {
    id: 'act-2',
    type: 'draft',
    title: 'Email draft generated for Northstar Interiors',
    description: 'Generated outreach referencing verified 404 finding and missing viewport.',
    timestamp: '45 mins ago',
    prospectId: 'pr-1'
  },
  {
    id: 'act-3',
    type: 'import',
    title: 'Imported 14 records from Navi Mumbai batch',
    description: 'Batch categorization: Interior Design & Architecture firms.',
    timestamp: '2 hours ago'
  },

  {
    id: 'act-5',
    type: 'status_change',
    title: 'Crestline Logistics marked as Contacted',
    description: 'Proposal prepared and verified for Crestline Logistics.',
    timestamp: '5 days ago',
    prospectId: 'pr-8'
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

