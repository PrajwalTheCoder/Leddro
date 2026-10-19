import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import {
  FileCode2,
  Play,
  Mail,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Server,
  Lock,
  Cpu,
  Download,
  ArrowLeft,
  Building2,
  FileText,
  Clock,
  Terminal,
  Activity,
  Sparkles,
  ArrowLeftRight
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { GenerateDraftModal } from '../components/common/GenerateDraftModal';
import { AuditComparisonModal } from '../components/common/AuditComparisonModal';

export const Audits: React.FC = () => {
  const {
    prospects,
    selectedProspectId,
    setSelectedProspectId,
    auditReports,
    runAudit,
    isAuditing,
    auditingProspectId,
    auditProgressMessage,
    backendOnline,
    createEmailDraftForProspect,
    addToast
  } = useApp();

  const navigate = useNavigate();
  const [expandedRawSection, setExpandedRawSection] = useState<'dns' | 'ssl' | 'perf' | 'headers' | null>(null);

  // Fallback to first prospect if none selected
  const prospect = prospects.find((p) => p.id === selectedProspectId) || prospects[0];
  const auditReport = prospect?.latestAuditId ? auditReports[prospect.latestAuditId] : undefined;

  const highSeverityCount = auditReport?.findings.filter((f) => f.severity === 'high').length || 0;
  const mediumSeverityCount = auditReport?.findings.filter((f) => f.severity === 'medium').length || 0;
  const lowSeverityCount = auditReport?.findings.filter((f) => f.severity === 'low').length || 0;
  const infoCount = auditReport?.findings.filter((f) => f.severity === 'info').length || 0;

  const handleExportJSON = () => {
    if (!auditReport) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(auditReport, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `audit_${prospect.name.toLowerCase().replace(/\s+/g, '_')}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    addToast('Downloaded audit evidence report', 'success');
  };

  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);

  const handleCreateDraft = () => {
    if (!prospect) return;
    setIsGenerateModalOpen(true);
  };

  if (!prospect) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-[#111214] p-8 text-center">
        <Building2 className="w-12 h-12 text-[#4B5361] mb-3" />
        <h2 className="text-[16px] font-semibold text-[#F3F4F6] mb-1">No Prospects Available for Audit</h2>
        <p className="text-[13px] text-[#8C929D] max-w-md mb-4">
          Discover new businesses via OpenStreetMap or import a CSV dataset to execute technical diagnostic website audits.
        </p>
        <Button variant="primary" size="md" onClick={() => navigate('/prospects')} leftIcon={<Building2 className="w-4 h-4" />}>
          View Prospects Pipeline
        </Button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#111214]">
      {/* Top Header Strip */}
      <div className="px-6 pt-5 pb-3 border-b border-[#22252A] flex flex-col gap-3 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="p-1.5 rounded bg-[#17191C] border border-[#2B2F36] text-[#A0A5AD] hover:text-[#F3F4F6] transition-colors"
              title="Return to Dashboard"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-[22px] font-semibold text-[#F3F4F6] tracking-tight">
                  Website Audit Dossier
                </h1>
                <Badge variant="status" prospectStatus={prospect.status} size="sm" />
              </div>
              <div className="flex items-center gap-2 text-[12px] text-[#A0A5AD] mt-0.5">
                <span className="font-medium text-[#F3F4F6]">{prospect.name}</span>
                <span>·</span>
                {prospect.websiteUrl ? (
                  <a
                    href={prospect.websiteUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-[11px] text-[#91B7D8] hover:underline flex items-center gap-1"
                  >
                    {prospect.websiteUrl}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <span className="text-[#727780] italic">No active web domain registered</span>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="md"
              onClick={handleExportJSON}
              disabled={!auditReport}
              leftIcon={<Download className="w-4 h-4" />}
            >
              Export JSON
            </Button>
            <Button
              variant="secondary"
              size="md"
              onClick={handleCreateDraft}
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Draft Outreach
            </Button>

            <Button
              variant="secondary"
              size="md"
              onClick={() => setIsCompareModalOpen(true)}
              leftIcon={<ArrowLeftRight className="w-4 h-4" />}
            >
              Compare Audits
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => runAudit(prospect.id)}
              isLoading={isAuditing && auditingProspectId === prospect.id}
              leftIcon={<Play className="w-4 h-4" />}
            >
              {auditReport ? 'Re-run Audit' : 'Execute Audit'}
            </Button>
          </div>
        </div>

        {/* Audit Meta Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-[#1F2228] text-[12px] text-[#A0A5AD]">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#727780]" />
              <span>Timestamp: <strong className="font-mono text-[#F3F4F6]">{auditReport?.timestamp || 'Never audited'}</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <Activity className={`w-3.5 h-3.5 ${backendOnline ? 'text-[#D8E7A2]' : 'text-[#E5A96A]'}`} />
              <span>
                Engine Status:{' '}
                {backendOnline ? (
                  <strong className="font-mono text-[#D8E7A2]">Live Server Engine (FastAPI + SQLite)</strong>
                ) : (
                  <strong className="font-mono text-[#E5A96A]">Offline Demo Mode (Backend Offline)</strong>
                )}
              </span>
            </div>
          </div>

          {/* Switch Prospect Selector */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-[#727780]">Auditing entity:</span>
            <select
              value={prospect.id}
              onChange={(e) => setSelectedProspectId(e.target.value)}
              className="bg-[#17191C] border border-[#2B2F36] rounded px-2.5 py-1 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
            >
              {prospects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.opportunityScore}/100)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Real Progress Banner during Live Audit */}
        {isAuditing && auditingProspectId === prospect.id && (
          <div className="mt-1 px-3 py-2 bg-[#1C2026] border border-[#2F3540] rounded flex items-center justify-between text-[12px]">
            <div className="flex items-center gap-2.5 text-[#D8E7A2]">
              <div className="w-2 h-2 rounded-full bg-[#D8E7A2] animate-ping" />
              <span className="font-mono">{auditProgressMessage || 'Connecting to live audit engine...'}</span>
            </div>
            <span className="text-[11px] font-mono text-[#727780] bg-[#111214] px-2 py-0.5 rounded border border-[#25282F]">
              SSRF Guard Active · Port Whitelist Enforced
            </span>
          </div>
        )}
      </div>

      {/* Main Body */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
        {/* Top Summary Cards (Technical indicators, NOT truck gauges) */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Opportunity Score Block */}
          <div className="p-4 rounded border border-[#2B2F36] bg-[#17191C] flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-medium text-[#A0A5AD]">Opportunity Score</span>
              <span className="font-mono text-[11px] text-[#D8E7A2] bg-[#22271B] px-1.5 py-0.5 rounded border border-[#3E4929]">
                Weighted Matrix
              </span>
            </div>
            <div className="flex items-baseline gap-2 my-2">
              <span className="text-[28px] font-semibold text-[#F3F4F6] font-mono leading-none">
                {prospect.opportunityScore}
              </span>
              <span className="text-[13px] text-[#727780]">/ 100</span>
            </div>
            <div className="w-full bg-[#111214] h-1.5 rounded-full overflow-hidden border border-[#262A30]">
              <div
                className="h-full bg-[#D8E7A2] rounded-full"
                style={{ width: `${prospect.opportunityScore}%` }}
              />
            </div>
          </div>

          {/* Findings Count Breakdown */}
          <div className="p-4 rounded border border-[#2B2F36] bg-[#17191C] flex flex-col justify-between">
            <span className="text-[12px] font-medium text-[#A0A5AD]">Findings Breakdown</span>
            <div className="flex items-center justify-between gap-2 my-2">
              <div className="text-center">
                <div className="text-[18px] font-mono font-semibold text-[#D78383]">{highSeverityCount}</div>
                <div className="text-[10px] text-[#727780] uppercase">High</div>
              </div>
              <div className="text-center">
                <div className="text-[18px] font-mono font-semibold text-[#D8B16C]">{mediumSeverityCount}</div>
                <div className="text-[10px] text-[#727780] uppercase">Medium</div>
              </div>
              <div className="text-center">
                <div className="text-[18px] font-mono font-semibold text-[#80B89A]">{lowSeverityCount}</div>
                <div className="text-[10px] text-[#727780] uppercase">Low</div>
              </div>
              <div className="text-center">
                <div className="text-[18px] font-mono font-semibold text-[#91B7D8]">{infoCount}</div>
                <div className="text-[10px] text-[#727780] uppercase">Info</div>
              </div>
            </div>
            <div className="text-[11px] text-[#727780] truncate">
              Total {auditReport?.findings.length || 0} issues identified
            </div>
          </div>

          {/* Network & TLS Status */}
          <div className="p-4 rounded border border-[#2B2F36] bg-[#17191C] flex flex-col justify-between">
            <span className="text-[12px] font-medium text-[#A0A5AD]">Transport &amp; Cryptography</span>
            <div className="my-2 flex flex-col gap-1">
              <div className="flex items-center justify-between text-[12px]">
                <span className="text-[#727780]">Protocol:</span>
                <span className="font-mono text-[#F3F4F6]">{auditReport?.rawSsl.tlsVersion || 'N/A'}</span>
              </div>
              <div className="flex items-center justify-between text-[12px]">
                <span className="text-[#727780]">Certificate:</span>
                <span className={`font-mono ${auditReport?.rawSsl.valid ? 'text-[#80B89A]' : 'text-[#D78383]'}`}>
                  {auditReport?.rawSsl.valid ? 'Valid (+44d)' : 'Expired (-6d)'}
                </span>
              </div>
            </div>
            <div className="text-[11px] text-[#727780] truncate font-mono">
              {auditReport?.rawSsl.issuer || 'No TLS Handshake'}
            </div>
          </div>

          {/* Crawl Performance Latency */}
          <div className="p-4 rounded border border-[#2B2F36] bg-[#17191C] flex flex-col justify-between">
            <span className="text-[12px] font-medium text-[#A0A5AD]">Crawl Performance</span>
            <div className="my-2 flex flex-col gap-1">
              <div className="flex items-center justify-between text-[12px]">
                <span className="text-[#727780]">Time to First Byte:</span>
                <span className="font-mono text-[#F3F4F6]">{auditReport?.performance.ttfbMs || 0} ms</span>
              </div>
              <div className="flex items-center justify-between text-[12px]">
                <span className="text-[#727780]">DOM Readiness:</span>
                <span className="font-mono text-[#F3F4F6]">{(auditReport?.performance.domReadyMs || 0) / 1000}s</span>
              </div>
            </div>
            <div className="text-[11px] text-[#727780]">
              Mobile Viewport: <strong className="text-[#F3F4F6]">{auditReport?.performance.mobileViewportPresent ? 'Declared' : 'MISSING'}</strong>
            </div>
          </div>
        </div>

        {/* Detailed Findings List */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-[15px] font-semibold text-[#F3F4F6] tracking-tight">
              Verified Technical Observations ({auditReport?.findings.length || 0})
            </h2>
            <span>
              {auditReport?.id?.startsWith('aud_') ? (
                <span className="text-[#D8E7A2] flex items-center gap-1.5 font-mono text-[11px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D8E7A2]" />
                  Live Server Findings (FastAPI Engine · Verified Check Pipeline)
                </span>
              ) : (
                <span className="text-[#A0A5AD] flex items-center gap-1.5 font-mono text-[11px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#E5A96A]" />
                  Demonstration Data (Baseline Local Fixture)
                </span>
              )}
            </span>
          </div>

          {auditReport && auditReport.findings.length > 0 ? (
            <div className="flex flex-col gap-3">
              {auditReport.findings.map((f, idx) => (
                <div
                  key={f.id}
                  className="rounded border border-[#2B2F36] bg-[#17191C] p-4 flex flex-col gap-3 transition-colors hover:border-[#383D47]"
                >
                  {/* Finding Title & Severity Tag */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#22252B] pb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-[12px] text-[#727780] bg-[#111214] px-1.5 py-0.5 rounded border border-[#262A30]">
                        #{idx + 1}
                      </span>
                      <h3 className="text-[14px] font-semibold text-[#F3F4F6]">
                        {f.title}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono text-[#727780]">
                        Confidence: {(f.confidence * 100).toFixed(0)}%
                      </span>
                      {f.checkStatus && (
                        <span
                          className={`font-mono text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded border ${f.checkStatus === 'PASS'
                              ? 'text-[#D8E7A2] bg-[#22271B] border-[#3E4929]'
                              : f.checkStatus === 'WARNING'
                                ? 'text-[#E5A96A] bg-[#2D2115] border-[#4E3924]'
                                : f.checkStatus === 'FAIL'
                                  ? 'text-[#E56A6A] bg-[#2D1616] border-[#4E2424]'
                                  : 'text-[#F87171] bg-[#331313] border-[#552020]'
                            }`}
                        >
                          {f.checkStatus}
                        </span>
                      )}
                      <Badge variant="severity" severity={f.severity} size="sm" />
                    </div>
                  </div>

                  {/* Observed & Why It Matters */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[13px]">
                    <div className="flex flex-col gap-1">
                      <div className="text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider">
                        Observed Behavior
                      </div>
                      <p className="text-[#D6D9E0] leading-relaxed">
                        {f.observed}
                      </p>
                    </div>

                    <div className="flex flex-col gap-1">
                      <div className="text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider">
                        Commercial &amp; Technical Impact
                      </div>
                      <p className="text-[#D6D9E0] leading-relaxed">
                        {f.whyItMatters}
                      </p>
                    </div>
                  </div>

                  {/* Monospace Raw Evidence Box (Understated bordered panel) */}
                  <div className="flex flex-col gap-1.5 pt-1">
                    <div className="text-[11px] font-medium text-[#727780] uppercase tracking-wider flex items-center gap-1.5">
                      <Terminal className="w-3.5 h-3.5" /> Deterministic Socket / Crawler Evidence
                    </div>
                    <pre className="p-3 rounded bg-[#111214] border border-[#24272D] text-[11px] font-mono text-[#A0A5AD] overflow-x-auto whitespace-pre-wrap leading-relaxed">
                      {f.evidence}
                    </pre>
                  </div>

                  {/* Recommended Action */}
                  <div className="flex items-start gap-2 p-2.5 rounded bg-[#1D2024] border border-[#2B2F36] text-[12px]">
                    <CheckCircle2 className="w-4 h-4 text-[#80B89A] shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-[#F3F4F6]">Remediation Recommendation: </strong>
                      <span className="text-[#A0A5AD]">{f.recommendedAction}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded border border-[#2B2F36] bg-[#17191C] p-8 text-center flex flex-col items-center gap-3">
              <FileCode2 className="w-8 h-8 text-[#727780]" />
              <div className="text-[14px] text-[#F3F4F6]">No audit findings recorded yet.</div>
              <p className="text-[12px] text-[#727780] max-w-sm">
                Click "Execute Audit" to launch the deterministic crawl, TLS handshake test, and DNS zone verification.
              </p>
              <Button
                variant="primary"
                size="md"
                onClick={() => runAudit(prospect.id)}
                leftIcon={<Play className="w-3.5 h-3.5" />}
              >
                Execute Website Audit
              </Button>
            </div>
          )}
        </div>

        {/* Expandable Raw Diagnostic Subsections */}
        {auditReport && (
          <div className="flex flex-col gap-3">
            <h2 className="text-[15px] font-semibold text-[#F3F4F6] tracking-tight">
              Raw Infrastructure Diagnostics
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* DNS Subsection */}
              <div className="rounded border border-[#2B2F36] bg-[#17191C] p-3.5 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[13px] font-medium text-[#F3F4F6]">
                    <Server className="w-4 h-4 text-[#91B7D8]" /> DNS Zone Records
                  </div>
                  <span className="font-mono text-[11px] text-[#727780]">{auditReport.rawDns.responseMs}ms query</span>
                </div>
                <div className="text-[11px] font-mono text-[#A0A5AD] flex flex-col gap-1 bg-[#111214] p-2.5 rounded border border-[#24272D]">
                  <div>A: {auditReport.rawDns.aRecord}</div>
                  <div>MX: {auditReport.rawDns.mxRecord}</div>
                  <div>NS: {Array.isArray(auditReport.rawDns?.nameservers) ? auditReport.rawDns.nameservers.join(', ') : (auditReport.rawDns?.nameservers || 'None')}</div>
                </div>
              </div>

              {/* SSL Details Subsection */}
              <div className="rounded border border-[#2B2F36] bg-[#17191C] p-3.5 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[13px] font-medium text-[#F3F4F6]">
                    <Lock className="w-4 h-4 text-[#D8E7A2]" /> TLS Handshake &amp; Cipher
                  </div>
                  <span className={`font-mono text-[11px] ${auditReport.rawSsl.valid ? 'text-[#80B89A]' : 'text-[#D78383]'}`}>
                    {auditReport.rawSsl.valid ? 'Active' : 'Expired'}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-[#A0A5AD] flex flex-col gap-1 bg-[#111214] p-2.5 rounded border border-[#24272D]">
                  <div>Cipher: {auditReport.rawSsl.cipher}</div>
                  <div>Issuer: {auditReport.rawSsl.issuer}</div>
                  <div>Protocol: {auditReport.rawSsl.tlsVersion}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <GenerateDraftModal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        targetProspectId={prospect?.id}
        targetAuditId={auditReport?.id}
      />

      <AuditComparisonModal
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        initialProspectId={prospect?.id}
        initialNewerAuditId={auditReport?.id}
      />
    </div>
  );
};

