import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  X, 
  Sparkles, 
  Play, 
  Mail, 
  ExternalLink, 
  Phone, 
  MapPin, 
  Calendar, 
  FileText, 
  AlertCircle, 
  CheckCircle2,
  ChevronRight,
  ShieldCheck,
  Send,
  History as HistoryIcon,
  BarChart3,
  ArrowLeftRight
} from 'lucide-react';
import { Button } from './Button';
import { Badge } from './Badge';
import { Prospect, AuditReport, EmailDraft } from '../../types';
import { useApp } from '../../context/AppContext';
import { ProspectScoringModal } from './ProspectScoringModal';
import { AuditComparisonModal } from './AuditComparisonModal';

interface ProspectDetailModalProps {
  prospect: Prospect | null;
  isOpen: boolean;
  onClose: () => void;
  onOpenGenerateModal: (prospectId: string) => void;
}

export const ProspectDetailModal: React.FC<ProspectDetailModalProps> = ({
  prospect,
  isOpen,
  onClose,
  onOpenGenerateModal
}) => {
  const { 
    auditReports, 
    emailDrafts, 
    setActiveDraftId, 
    runAudit, 
    isAuditing, 
    auditingProspectId,
    suppressions,
    addSuppression,
    removeSuppression,
    emailHistory
  } = useApp();
  const navigate = useNavigate();

  const [isScoringModalOpen, setIsScoringModalOpen] = useState(false);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);

  if (!isOpen || !prospect) return null;

  const latestAudit: AuditReport | undefined = prospect.latestAuditId
    ? auditReports[prospect.latestAuditId]
    : undefined;

  const prospectDrafts = emailDrafts.filter((d) => d.prospectId === prospect.id);
  const prospectDispatches = emailHistory.filter((h) => h.prospectId === prospect.id);

  const prospectEmail = prospect.email;
  const suppressionRecord = prospectEmail
    ? suppressions.find((s) => {
        const clean = prospectEmail.toLowerCase();
        const domain = clean.split('@')[1];
        const rec = s.email_or_domain.toLowerCase();
        return rec === clean || rec === domain || rec === `@${domain}`;
      })
    : null;

  const handleOpenDraft = (draftId: string) => {
    setActiveDraftId(draftId);
    onClose();
    navigate('/drafts');
  };

  const handleOpenAudit = () => {
    onClose();
    navigate('/audits');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="w-full max-w-2xl rounded border border-[#30343A] bg-[#17191C] shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#24272D] flex items-center justify-between bg-[#1A1C20]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-[#1D2024] border border-[#30343A] flex items-center justify-center text-[#D8E7A2]">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-[16px] font-semibold text-[#F3F4F6] tracking-tight">{prospect.name}</h2>
                <Badge variant="status" prospectStatus={prospect.status} size="sm" />
              </div>
              <div className="flex items-center gap-2 text-[12px] text-[#A0A5AD] mt-0.5">
                <span>{prospect.category}</span>
                <span>·</span>
                <span>{prospect.location.city}, {prospect.location.state}</span>
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-[#727780] hover:text-[#F3F4F6] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-5 text-[12px]">
          {/* Business & Discovery Dossier */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded border border-[#2B2F36] bg-[#141618] p-3.5 flex flex-col gap-2">
              <span className="text-[11px] font-medium text-[#727780] uppercase tracking-wider">
                Digital Presence &amp; Verification
              </span>
              <div className="flex items-center justify-between pt-1">
                <span className="text-[#A0A5AD]">Website Condition:</span>
                <Badge variant="website" websiteStatus={prospect.websiteStatus} size="sm" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Domain:</span>
                {prospect.websiteUrl ? (
                  <a
                    href={prospect.websiteUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-[#D8E7A2] hover:underline flex items-center gap-1"
                  >
                    <span>{prospect.websiteUrl.replace(/https?:\/\//, '')}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <span className="text-[#727780] italic">Not listed</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Source:</span>
                <span className="font-mono text-[#A0A5AD]">{prospect.sourceProvider || 'Local Directory'}</span>
              </div>
            </div>

            <div className="rounded border border-[#2B2F36] bg-[#141618] p-3.5 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-[#727780] uppercase tracking-wider">
                  Direct Contact Information
                </span>
                {prospect.email && (
                  suppressionRecord ? (
                    <button
                      onClick={() => removeSuppression(suppressionRecord.id)}
                      className="text-[10px] font-mono text-[#D78383] hover:underline"
                      title={`Suppressed: ${suppressionRecord.reason}`}
                    >
                      [Remove Opt-out]
                    </button>
                  ) : (
                    <button
                      onClick={() => prospectEmail && addSuppression(prospectEmail, 'User-initiated opt-out')}
                      className="text-[10px] font-mono text-[#727780] hover:text-[#D78383] transition-colors"
                    >
                      [Mark Opted-out]
                    </button>
                  )
                )}
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-[#727780]">Email:</span>
                <div className="flex items-center gap-1.5 font-mono text-[#F3F4F6]">
                  <span>{prospect.email || 'Not listed'}</span>
                  {suppressionRecord && (
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-[#321A1A] text-[#D78383] border border-[#522525]">
                      OPTED OUT
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Provenance:</span>
                <span className="font-mono text-[11px] text-[#A0A5AD]">
                  {prospect.email
                    ? (prospect.sourceProvider ? `Discovered via ${prospect.sourceProvider}` : 'User-entered / local data')
                    : 'No address recorded'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Phone:</span>
                <span className="font-mono text-[#F3F4F6]">{prospect.phone || 'Not listed'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Opportunity Score:</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[#D8E7A2] bg-[#22271B] px-1.5 py-0.5 rounded border border-[#3E4929]">
                    {prospect.opportunityScore}/100
                  </span>
                  {prospect.scoring?.priorityLabel && (
                    <span className="font-mono text-[10px] text-[#A0A5AD] px-1.5 py-0.2 rounded bg-[#1A1C20] border border-[#2B2F36]">
                      {prospect.scoring.priorityLabel}
                    </span>
                  )}
                  <button
                    onClick={() => setIsScoringModalOpen(true)}
                    className="flex items-center gap-1 text-[11px] font-medium text-[#D8E7A2] hover:underline cursor-pointer bg-[#22271B] px-2 py-0.5 rounded border border-[#3E4929]"
                  >
                    <BarChart3 className="w-3 h-3" />
                    <span>Explain Score</span>
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Data Confidence:</span>
                <span className="font-mono text-[11px] text-[#F3F4F6]">
                  {prospect.scoring ? `${prospect.scoring.confidenceScore}/100` : 'Baseline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Contact Readiness:</span>
                <span className="font-mono text-[11px] capitalize text-[#A0A5AD]">
                  {prospect.scoring ? prospect.scoring.contactReadiness : (prospect.email ? 'unverified' : 'absent')}
                </span>
              </div>
            </div>
          </div>

          {/* Audit Status & Findings */}
          <div className="rounded border border-[#2B2F36] bg-[#141618] p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-[#22252A] pb-2.5">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-[#D8E7A2]" />
                <span className="text-[13px] font-medium text-[#F3F4F6]">Website Audit Dossier</span>
              </div>
              {latestAudit ? (
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-[#80B89A]">Score: {latestAudit.overallScore}/100</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsCompareModalOpen(true)}
                    leftIcon={<ArrowLeftRight className="w-3.5 h-3.5" />}
                  >
                    Compare
                  </Button>
                  <Button variant="ghost" size="sm" onClick={handleOpenAudit}>
                    View Dossier
                  </Button>
                </div>
              ) : (
                <span className="text-[11px] text-[#727780] italic">No audit performed yet</span>
              )}
            </div>

            {latestAudit && latestAudit.findings && latestAudit.findings.length > 0 ? (
              <div className="flex flex-col gap-2">
                <span className="text-[11px] text-[#727780]">
                  Verified technical issues discovered on domain ({latestAudit.findings.length} findings):
                </span>
                <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto">
                  {latestAudit.findings.map((f) => (
                    <div
                      key={f.id}
                      className="p-2.5 rounded bg-[#1A1C20] border border-[#26292F] flex items-center justify-between"
                    >
                      <div className="flex flex-col gap-0.5 truncate pr-2">
                        <span className="font-medium text-[#F3F4F6]">{f.title}</span>
                        <span className="text-[11px] text-[#727780] truncate">{f.observed}</span>
                      </div>
                      <Badge variant="severity" severity={f.severity} size="sm" />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between text-[11px] text-[#727780]">
                <span>Run a deterministic audit to discover verified technical improvement opportunities.</span>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!prospect.websiteUrl || isAuditing}
                  isLoading={isAuditing && auditingProspectId === prospect.id}
                  onClick={() => runAudit(prospect.id)}
                  leftIcon={<Play className="w-3.5 h-3.5" />}
                >
                  Run Audit
                </Button>
              </div>
            )}
          </div>

          {/* Existing Saved Drafts for this Prospect */}
          <div className="rounded border border-[#2B2F36] bg-[#141618] p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-[#22252A] pb-2.5">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-[#D8E7A2]" />
                <span className="text-[13px] font-medium text-[#F3F4F6]">Saved Email Drafts ({prospectDrafts.length})</span>
              </div>
            </div>

            {prospectDrafts.length > 0 ? (
              <div className="flex flex-col gap-2">
                {prospectDrafts.map((d) => (
                  <div
                    key={d.id}
                    onClick={() => handleOpenDraft(d.id)}
                    className="p-3 rounded bg-[#1A1C20] border border-[#26292F] hover:border-[#3E4550] cursor-pointer flex items-center justify-between transition-colors"
                  >
                    <div className="flex flex-col gap-1 truncate pr-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-[#F3F4F6]">{d.subject}</span>
                        <span className="font-mono text-[10px] text-[#D8E7A2] bg-[#22271B] px-1.5 py-0.2 rounded border border-[#364024]">
                          {d.status.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-[11px] text-[#727780] truncate font-mono">
                        {d.body.substring(0, 90)}...
                      </span>
                    </div>
                    <Button variant="ghost" size="sm" leftIcon={<ChevronRight className="w-3.5 h-3.5" />}>
                      Open
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-[11px] text-[#727780] italic">
                No email drafts created yet for this prospect. Select "Generate Email Draft" to create one.
              </div>
            )}
          </div>

          {/* Outbound Dispatch History for this Prospect */}
          <div className="rounded border border-[#2B2F36] bg-[#141618] p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-[#22252A] pb-2.5">
              <div className="flex items-center gap-2">
                <HistoryIcon className="w-4 h-4 text-[#D8E7A2]" />
                <span className="text-[13px] font-medium text-[#F3F4F6]">Outbound Send History ({prospectDispatches.length})</span>
              </div>
            </div>

            {prospectDispatches.length > 0 ? (
              <div className="flex flex-col gap-2">
                {prospectDispatches.map((h) => (
                  <div
                    key={h.id}
                    className="p-3 rounded bg-[#1A1C20] border border-[#26292F] flex items-center justify-between"
                  >
                    <div className="flex flex-col gap-1 truncate pr-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-[#F3F4F6] truncate max-w-sm">{h.subject}</span>
                        <span className={`inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-mono border ${
                          h.status === 'submitted' || h.status === 'sent'
                            ? 'bg-[#18261F] text-[#80B89A] border-[#253D30]'
                            : h.status === 'failed'
                            ? 'bg-[#2A1818] text-[#D78383] border-[#4A2626]'
                            : h.status === 'uncertain'
                            ? 'bg-[#2C2415] text-[#E5A93C] border-[#52411E]'
                            : 'bg-[#2A2417] text-[#D8B16C] border-[#4A3D22]'
                        }`}>
                          <span className={`w-1 h-1 rounded-full ${
                            h.status === 'submitted' || h.status === 'sent'
                              ? 'bg-[#80B89A]'
                              : h.status === 'failed'
                              ? 'bg-[#D78383]'
                              : h.status === 'uncertain'
                              ? 'bg-[#E5A93C]'
                              : 'bg-[#D8B16C]'
                          }`} />
                          {h.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[11px] font-mono text-[#727780]">
                        <span>{h.date}</span>
                        {h.providerMessageId ? (
                          <span className="text-[#D8E7A2]">Gmail ID: {h.providerMessageId}</span>
                        ) : (
                          <span className="italic">No provider receipt</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-[11px] text-[#727780] italic">
                No outbound emails dispatched to this prospect yet.
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-3.5 border-t border-[#24272D] flex items-center justify-between bg-[#1A1C20]">
          <Button variant="ghost" size="md" onClick={onClose}>
            Close
          </Button>

          <div className="flex items-center gap-2.5">
            {prospect.websiteUrl && (
              <Button
                variant="secondary"
                size="md"
                disabled={isAuditing}
                isLoading={isAuditing && auditingProspectId === prospect.id}
                onClick={() => runAudit(prospect.id)}
                leftIcon={<Play className="w-4 h-4" />}
              >
                {latestAudit ? 'Re-run Audit' : 'Audit Website'}
              </Button>
            )}
            <Button
              variant="primary"
              size="md"
              onClick={() => {
                onClose();
                onOpenGenerateModal(prospect.id);
              }}
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Generate Email Draft
            </Button>
          </div>
        </div>
      </div>
      <ProspectScoringModal
        isOpen={isScoringModalOpen}
        onClose={() => setIsScoringModalOpen(false)}
        prospect={prospect}
      />
      <AuditComparisonModal
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        initialProspectId={prospect?.id}
        initialNewerAuditId={prospect?.latestAuditId}
      />
    </div>
  );
};
