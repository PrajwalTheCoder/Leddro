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
  ArrowLeftRight,
  MessageSquare,
  Globe,
  Search,
  Compass,
  Loader2,
  Share2
} from 'lucide-react';
import { Button } from './Button';
import { Badge } from './Badge';
import { Prospect, AuditReport, EmailDraft } from '../../types';
import { useApp } from '../../context/AppContext';
import { ProspectScoringModal } from './ProspectScoringModal';
import { AuditComparisonModal } from './AuditComparisonModal';
import { EvidenceTrustPanel } from './EvidenceTrustPanel';

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
    emailHistory,
    refreshProspects,
    refreshDrafts,
    addToast
  } = useApp();
  const navigate = useNavigate();

  const [isScoringModalOpen, setIsScoringModalOpen] = useState(false);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);
  const [isDeepSearching, setIsDeepSearching] = useState(false);
  const [deepSearchResult, setDeepSearchResult] = useState<any>(null);

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

  const handleDeepSearch = async () => {
    if (!prospect) return;
    setIsDeepSearching(true);
    try {
      const res = await fetch('/api/enrichment/deep-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prospect_id: prospect.id,
          business_name: prospect.name,
          location: prospect.location.city,
          phone: prospect.phone
        })
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(
          (errBody && errBody.detail) ||
          `Server returned ${res.status}. This is a lookup failure, not proof that no contact exists; retry shortly or check provider status in Settings.`
        );
      }
      const data = await res.json();
      setDeepSearchResult(data);
      await refreshProspects();
      await refreshDrafts();
      if (data.primary_email) {
        addToast(`Found email ${data.primary_email} (unverified until you inspect its source)`, 'success');
      } else if (data.success) {
        addToast(`Discovered online profiles for ${prospect.name}`, 'info');
      } else {
        addToast(`No new public contact info found for ${prospect.name}`, 'warning');
      }
    } catch (err: any) {
      addToast(`Deep search failed: ${err.message}`, 'error');
    } finally {
      setIsDeepSearching(false);
    }
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
                    ? (prospect.contactProvenance?.status
                        ? `${prospect.contactProvenance.source_type || 'source'} · ${prospect.contactProvenance.status}`
                        : (prospect.sourceProvider ? `Discovered via ${prospect.sourceProvider} (unverified)` : 'No provenance recorded'))
                    : 'No address recorded'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Phone:</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[#F3F4F6]">{prospect.phone || 'Not listed'}</span>
                  {prospect.phone && (
                    <div className="flex items-center gap-1">
                      <a
                        href={`tel:${prospect.phone.replace(/[^0-9+]/g, '')}`}
                        className="px-1.5 py-0.5 rounded bg-[#1D2530] text-[#91B7D8] hover:bg-[#253242] text-[10px] font-mono border border-[#2B3A4F] transition-colors"
                        title="Call business phone"
                      >
                        Call
                      </a>
                      <a
                        href={`https://wa.me/${prospect.phone.replace(/[^0-9]/g, '')}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-1.5 py-0.5 rounded bg-[#18261F] text-[#80B89A] hover:bg-[#1F3329] text-[10px] font-mono border border-[#253D30] transition-colors"
                        title="Chat on WhatsApp"
                      >
                        WhatsApp
                      </a>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-[#22252A]">
                <span className="text-[#727780]">Lead Intelligence:</span>
                <button
                  onClick={handleDeepSearch}
                  disabled={isDeepSearching}
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-[#D8E7A2] hover:text-[#E8F5B8] bg-[#22271B] hover:bg-[#2C3423] px-2.5 py-1 rounded border border-[#3E4929] transition-all cursor-pointer disabled:opacity-50"
                  title="Search Facebook, Instagram, Google Dorks, Justdial, and FSSAI records"
                >
                  {isDeepSearching ? (
                    <Loader2 className="w-3 h-3 animate-spin text-[#D8E7A2]" />
                  ) : (
                    <Search className="w-3 h-3 text-[#D8E7A2]" />
                  )}
                  <span>{isDeepSearching ? 'Deep Searching...' : 'Deep Search Contacts'}</span>
                </button>
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

          <EvidenceTrustPanel prospect={prospect} />

          {/* Pillar 1-5 Deep Search & Intelligence Dossier Panel */}
          {(deepSearchResult || isDeepSearching) && (
            <div className="rounded border border-[#3E4929] bg-[#171D18] p-4 flex flex-col gap-3 transition-all animate-fadeIn">
              <div className="flex items-center justify-between border-b border-[#283522] pb-2">
                <div className="flex items-center gap-2">
                  <Compass className="w-4 h-4 text-[#D8E7A2]" />
                  <span className="text-[13px] font-semibold text-[#F3F4F6]">
                    Deep Digital Footprint &amp; Multi-Channel Intelligence
                  </span>
                </div>
                {isDeepSearching && (
                  <span className="inline-flex items-center gap-1.5 font-mono text-[10px] text-[#D8E7A2] bg-[#22271B] px-2 py-0.5 rounded border border-[#364024]">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Scanning 5 Discovery Channels...
                  </span>
                )}
              </div>

              {isDeepSearching ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-[#A0A5AD] font-mono py-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#D8E7A2] animate-ping" />
                    <span>Facebook Business &amp; Instagram Bios</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#D8E7A2] animate-ping" />
                    <span>Search Engine Dorking (Gmail / Yahoo)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#D8E7A2] animate-ping" />
                    <span>WhatsApp Business Metadata Lookup</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#D8E7A2] animate-ping" />
                    <span>Justdial, Zomato &amp; Swiggy Listings</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#D8E7A2] animate-ping" />
                    <span>FSSAI Food License &amp; GSTIN Filings</span>
                  </div>
                </div>
              ) : deepSearchResult ? (
                <div className="flex flex-col gap-3 text-[12px]">
                  {/* Summary Callout */}
                  <div className="p-2.5 rounded bg-[#1D251E] border border-[#2B3B28] text-[11px] flex items-center justify-between">
                    <span className="text-[#A5C799]">
                      {deepSearchResult.message || 'Discovery completed.'}
                    </span>
                    {deepSearchResult.primary_email && (
                      <span className="font-mono text-[10px] bg-[#18261F] text-[#80B89A] border border-[#253D30] px-2 py-0.5 rounded flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Domain has MX records (mailbox unconfirmed)
                      </span>
                    )}
                  </div>

                  {/* Channel Badges Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {/* Social Profiles */}
                    <div className="p-2.5 rounded bg-[#131713] border border-[#263321] flex flex-col gap-1.5">
                      <span className="text-[10px] font-mono uppercase text-[#727780]">
                        Social Storefronts (FB &amp; IG)
                      </span>
                      <div className="flex items-center gap-2 flex-wrap">
                        {deepSearchResult.social_profiles?.facebook ? (
                          <a
                            href={deepSearchResult.social_profiles.facebook}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#1C2A3A] text-[#91B7D8] hover:bg-[#253A52] text-[11px] font-mono border border-[#2B3F56] transition-colors"
                          >
                            <span>Facebook Page</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-[11px] text-[#727780] italic">No Facebook</span>
                        )}
                        {deepSearchResult.social_profiles?.instagram ? (
                          <a
                            href={deepSearchResult.social_profiles.instagram}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#331C2D] text-[#D891C8] hover:bg-[#47253E] text-[11px] font-mono border border-[#522B47] transition-colors"
                          >
                            <span>Instagram Bio</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-[11px] text-[#727780] italic">No Instagram</span>
                        )}
                      </div>
                    </div>

                    {/* WhatsApp Business */}
                    <div className="p-2.5 rounded bg-[#131713] border border-[#263321] flex flex-col gap-1.5">
                      <span className="text-[10px] font-mono uppercase text-[#727780]">
                        WhatsApp Business
                      </span>
                      {deepSearchResult.whatsapp ? (
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[#F3F4F6]">
                            {deepSearchResult.whatsapp.phone_e164}
                          </span>
                          <a
                            href={deepSearchResult.whatsapp.wa_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#18261F] text-[#80B89A] hover:bg-[#20362A] text-[11px] font-mono border border-[#253D30] transition-colors"
                          >
                            <MessageSquare className="w-3 h-3" />
                            <span>Chat on WhatsApp</span>
                          </a>
                        </div>
                      ) : (
                        <span className="text-[11px] text-[#727780] italic">No WhatsApp phone recorded</span>
                      )}
                    </div>

                    {/* Indian Directories */}
                    <div className="p-2.5 rounded bg-[#131713] border border-[#263321] flex flex-col gap-1.5">
                      <span className="text-[10px] font-mono uppercase text-[#727780]">
                        Local Directories (Justdial / Zomato / Swiggy)
                      </span>
                      <div className="flex items-center gap-2 flex-wrap">
                        {deepSearchResult.social_profiles?.justdial && (
                          <a
                            href={deepSearchResult.social_profiles.justdial}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#2D2418] text-[#D8B16C] hover:bg-[#3D301E] text-[11px] font-mono border border-[#4A3A22] transition-colors"
                          >
                            <span>Justdial</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                        {deepSearchResult.social_profiles?.zomato && (
                          <a
                            href={deepSearchResult.social_profiles.zomato}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#311C1C] text-[#D88282] hover:bg-[#452424] text-[11px] font-mono border border-[#522929] transition-colors"
                          >
                            <span>Zomato</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                        {deepSearchResult.social_profiles?.swiggy && (
                          <a
                            href={deepSearchResult.social_profiles.swiggy}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#332215] text-[#D89B66] hover:bg-[#472E1B] text-[11px] font-mono border border-[#52351E] transition-colors"
                          >
                            <span>Swiggy</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                        {!deepSearchResult.social_profiles?.justdial && !deepSearchResult.social_profiles?.zomato && !deepSearchResult.social_profiles?.swiggy && (
                          <span className="text-[11px] text-[#727780] italic">No local directory matched</span>
                        )}
                      </div>
                    </div>

                    {/* Government / FSSAI / Discovered Web */}
                    <div className="p-2.5 rounded bg-[#131713] border border-[#263321] flex flex-col gap-1.5">
                      <span className="text-[10px] font-mono uppercase text-[#727780]">
                        Government &amp; Discovered Web
                      </span>
                      <div className="flex items-center gap-2 flex-wrap">
                        {deepSearchResult.fssai_info ? (
                          <span className="font-mono text-[10px] bg-[#22271B] text-[#D8E7A2] border border-[#3E4929] px-2 py-0.5 rounded">
                            {deepSearchResult.fssai_info.type}: {deepSearchResult.fssai_info.license_number || deepSearchResult.fssai_info.gstin}
                          </span>
                        ) : (
                          <span className="text-[11px] text-[#727780] italic">No FSSAI/GSTIN recorded</span>
                        )}
                        {deepSearchResult.discovered_website && (
                          <a
                            href={deepSearchResult.discovered_website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-[11px] text-[#D8E7A2] hover:underline flex items-center gap-1"
                          >
                            <span>{deepSearchResult.discovered_website.replace(/https?:\/\//, '')}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          )}

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
            <Button
              variant="secondary"
              size="md"
              disabled={isDeepSearching}
              isLoading={isDeepSearching}
              onClick={handleDeepSearch}
              leftIcon={<Search className="w-4 h-4 text-[#D8E7A2]" />}
              title="Search Facebook, Instagram, Google Dorks, WhatsApp & FSSAI"
            >
              Deep Search Intel
            </Button>
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
