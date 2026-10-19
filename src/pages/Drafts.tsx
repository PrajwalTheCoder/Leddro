import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import {
  Mail,
  Save,
  Eye,
  CheckCircle2,
  AlertCircle,
  Building2,
  FileText,
  Sparkles,
  ExternalLink,
  X,
  Copy,
  Trash2,
  RefreshCw,
  Plus,
  ShieldCheck,
  AlertTriangle,
  Phone,
  MessageSquare,
  Globe,
  Search
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { GenerateDraftModal } from '../components/common/GenerateDraftModal';

export const Drafts: React.FC = () => {
  const {
    emailDrafts,
    activeDraft,
    setActiveDraftId,
    saveEmailDraft,
    deleteEmailDraft,
    refreshDrafts,
    prospects,
    auditReports,
    setSelectedProspectId,
    googleStatus,
    emailDispatchStatus,
    sendEmailDraft,
    suppressions,
    addToast
  } = useApp();

  const navigate = useNavigate();

  // Current draft fields
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isSaving, setIsSaving] = useState(false);

  // Send Email Modal state
  const [isSendModalOpen, setIsSendModalOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [explicitConfirm, setExplicitConfirm] = useState(false);
  const [sendResult, setSendResult] = useState<{ success: boolean; messageId?: string; provider?: string; error?: string } | null>(null);

  // Modals
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [isRegenerateModalOpen, setIsRegenerateModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenPurpose, setRegenPurpose] = useState<string>('website_improvement');
  const [regenTone, setRegenTone] = useState<string>('professional');
  const [regenInstructions, setRegenInstructions] = useState('');

  // Fetch drafts on mount
  useEffect(() => {
    refreshDrafts();
  }, []);


  // Sync state with active draft
  useEffect(() => {
    if (activeDraft) {
      setRecipient(activeDraft.recipientEmail);
      setSubject(activeDraft.subject);
      setBody(activeDraft.body);
      if (activeDraft.outreachPurpose) setRegenPurpose(activeDraft.outreachPurpose);
      if (activeDraft.writingTone) setRegenTone(activeDraft.writingTone);
    } else {
      setRecipient('');
      setSubject('');
      setBody('');
    }
  }, [activeDraft]);

  const associatedProspect = activeDraft
    ? prospects.find((p) => p.id === activeDraft.prospectId)
    : undefined;

  const associatedAudit = (activeDraft?.auditId && auditReports[activeDraft.auditId])
    || (associatedProspect?.latestAuditId && auditReports[associatedProspect.latestAuditId]);

  // Check if content has been modified by operator
  const isDirty = activeDraft ? (subject !== activeDraft.subject || body !== activeDraft.body) : false;

  const handleSave = async () => {
    if (!activeDraft) return;
    setIsSaving(true);
    await saveEmailDraft({
      ...activeDraft,
      recipientEmail: recipient,
      subject,
      body,
      status: activeDraft.status === 'draft' && isDirty ? 'edited' : activeDraft.status
    });
    setIsSaving(false);
  };

  const handleToggleApproved = async () => {
    if (!activeDraft) return;
    const nextStatus = activeDraft.status === 'approved' ? 'draft' : 'approved';
    setIsSaving(true);
    await saveEmailDraft({
      ...activeDraft,
      recipientEmail: recipient,
      subject,
      body,
      status: nextStatus
    });
    setIsSaving(false);
    if (nextStatus === 'approved') {
      addToast('Draft marked as Approved. You can now authorize sending via Gmail.', 'success');
    } else {
      addToast('Draft reverted to Draft status.', 'info');
    }
  };

  // Contact Enrichment & Real Phone Handlers
  const [isExtractingContacts, setIsExtractingContacts] = useState(false);
  const [enrichmentSource, setEnrichmentSource] = useState<string | null>(null);

  const realPhone = associatedProspect?.phone?.trim() || null;
  const telLink = realPhone ? `tel:${realPhone.replace(/[^0-9+]/g, '')}` : null;
  const waDigits = realPhone ? realPhone.replace(/[^0-9]/g, '') : null;
  const waLink = waDigits ? `https://wa.me/${waDigits}` : null;
  const suggestedDomain = associatedProspect?.websiteUrl
    ? associatedProspect.websiteUrl.replace(/https?:\/\//, '').replace(/^www\./, '').split('/')[0].toLowerCase()
    : null;
  const waPitchLink = waDigits
    ? `https://wa.me/${waDigits}?text=${encodeURIComponent(`Hi ${associatedProspect?.name || 'there'},\n\n${subject}\n\n${body}`)}`
    : waLink;

  const handleExtractFromWebsite = async () => {
    if (!associatedProspect?.websiteUrl) {
      addToast('No website URL listed for this prospect.', 'error');
      return;
    }
    setIsExtractingContacts(true);
    try {
      const res = await fetch('/api/enrichment/scrape-website', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: associatedProspect.websiteUrl,
          prospect_id: associatedProspect.id
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Website scraping failed');

      if (data.primary_email) {
        setRecipient(data.primary_email);
        setEnrichmentSource('website_scraper');
        addToast(`Found authentic verified email: ${data.primary_email}`, 'success');
        await refreshDrafts();
      } else {
        addToast(`Crawled ${associatedProspect.websiteUrl} but found no email with active MX records.`, 'info');
      }
    } catch (err: any) {
      addToast(`Website scraper error: ${err.message}`, 'error');
    } finally {
      setIsExtractingContacts(false);
    }
  };

  const handleFindViaHunter = async () => {
    if (!associatedProspect?.id) return;
    setIsExtractingContacts(true);
    try {
      const res = await fetch('/api/enrichment/find-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prospect_id: associatedProspect.id })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Contact lookup failed');

      if (data.success && data.email) {
        setRecipient(data.email);
        setEnrichmentSource(data.source);
        addToast(`Found verified email via ${data.source}: ${data.email}`, 'success');
        await refreshDrafts();
      } else {
        addToast(data.message || 'No verified email found.', 'info');
      }
    } catch (err: any) {
      addToast(`Enrichment error: ${err.message}`, 'error');
    } finally {
      setIsExtractingContacts(false);
    }
  };

  const isSenderConfigured = Boolean(
    emailDispatchStatus?.is_ready ||
    googleStatus?.is_connected ||
    (emailDispatchStatus?.method === 'smtp' && emailDispatchStatus.sender_email)
  );

  const activeProviderName = emailDispatchStatus?.provider_name || (googleStatus?.is_connected ? 'Gmail API (OAuth 2.0)' : 'Gmail SMTP');
  const activeSenderEmail = emailDispatchStatus?.sender_email || googleStatus?.email || 'Authenticated Account';
  const isSMTP = emailDispatchStatus?.method === 'smtp' || (!googleStatus?.is_connected && Boolean(emailDispatchStatus?.smtp_configured));

  const isRecipientSuppressed = () => {
    if (!recipient) return null;
    const clean = recipient.trim().toLowerCase();
    const domain = clean.split('@')[1];
    return suppressions.find((s) => {
      const entry = s.email_or_domain.toLowerCase();
      return entry === clean || entry === domain || entry === `@${domain}`;
    });
  };

  const handleOpenSendModal = () => {
    if (!activeDraft) return;
    if (activeDraft.status === 'uncertain') {
      addToast('Cannot send: This draft is in an uncertain delivery state. Please check your Sent folder.', 'error');
      return;
    }
    if (activeDraft.status === 'submitted') {
      addToast('Cannot send: This draft has already been submitted.', 'error');
      return;
    }
    if (!isSenderConfigured) {
      addToast('Cannot send: No email provider configured. Configure SMTP or connect Google in Integrations.', 'error');
      navigate('/integrations');
      return;
    }
    if (!recipient.trim()) {
      addToast('No recipient email address is available. Add and verify the recipient address before sending.', 'error');
      return;
    }
    const sup = isRecipientSuppressed();
    if (sup) {
      addToast(`Outbound dispatch blocked: Recipient '${recipient}' is suppressed (${sup.reason}).`, 'error');
      return;
    }
    setExplicitConfirm(false);
    setSendResult(null);
    setIsSendModalOpen(true);
  };

  const handleExecuteSend = async () => {
    if (!activeDraft || !explicitConfirm) return;
    setIsSending(true);
    setSendResult(null);
    try {
      const res = await sendEmailDraft({
        draftId: activeDraft.id,
        recipient: recipient.trim(),
        subject: subject.trim(),
        body: body.trim(),
        confirmed: true
      });
      setSendResult(res);
    } finally {
      setIsSending(false);
    }
  };


  const handleCopySubject = () => {
    navigator.clipboard.writeText(subject);
    addToast('Subject line copied to clipboard', 'info');
  };

  const handleCopyBody = () => {
    navigator.clipboard.writeText(body);
    addToast('Email body copied to clipboard', 'info');
  };

  const handleOpenProspect = () => {
    if (associatedProspect) {
      setSelectedProspectId(associatedProspect.id);
      navigate('/prospects');
    }
  };

  const handleConfirmRegenerate = async () => {
    if (!activeDraft) return;
    setIsRegenerating(true);
    try {
      const response = await fetch(`/api/drafts/${activeDraft.id}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          purpose: regenPurpose,
          tone: regenTone,
          custom_instructions: regenInstructions.trim() || undefined,
          privacy_consent: true
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Regeneration failed (${response.status})`);
      }

      const updatedDraft = await response.json();
      await refreshDrafts();
      setSubject(updatedDraft.subject);
      setBody(updatedDraft.body);
      setIsRegenerateModalOpen(false);
      addToast('Draft successfully regenerated with updated parameters', 'success');
    } catch (err: any) {
      addToast(`Regeneration failed: ${err.message}`, 'error');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!activeDraft) return;
    await deleteEmailDraft(activeDraft.id);
    setIsDeleteModalOpen(false);
  };

  // Filter drafts list
  const filteredDrafts = emailDrafts.filter((d) => {
    if (statusFilter === 'all') return true;
    return d.status === statusFilter;
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#111214]">
      {/* Header */}
      <div className="px-6 pt-5 pb-3 border-b border-[#22252A] flex flex-col gap-3 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-[24px] font-semibold text-[#F3F4F6] tracking-tight">
                Email Draft Editor
              </h1>
              <span className="font-mono text-[11px] text-[#80B89A] bg-[#18261F] px-2 py-0.5 rounded border border-[#253D30]">
                Phase 6: Gmail API Active
              </span>
            </div>
            <p className="text-[12px] text-[#A0A5AD] mt-0.5">
              Review, edit, explicitly approve, and dispatch personalized outreach letters anchored in verified website audit findings.
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="md"
              onClick={() => setIsGenerateModalOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              New Draft
            </Button>
            {activeDraft && (
              <>
                <Button
                  variant="secondary"
                  size="md"
                  onClick={() => setIsPreviewMode(!isPreviewMode)}
                  leftIcon={<Eye className="w-4 h-4" />}
                >
                  {isPreviewMode ? 'Edit Draft' : 'Preview'}
                </Button>
                <Button
                  variant="secondary"
                  size="md"
                  isLoading={isSaving}
                  onClick={handleSave}
                  leftIcon={<Save className="w-4 h-4" />}
                >
                  Save Draft
                </Button>
                <Button
                  variant={activeDraft.status === 'approved' ? 'secondary' : 'primary'}
                  size="md"
                  onClick={handleToggleApproved}
                  leftIcon={<CheckCircle2 className="w-4 h-4" />}
                >
                  {activeDraft.status === 'approved' ? 'Mark as Draft' : 'Approve Draft'}
                </Button>
                {activeDraft.status === 'submitted' ? (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#18261F] border border-[#253D30] text-[12px] text-[#80B89A] font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Sent</span>
                  </div>
                ) : activeDraft.status === 'uncertain' ? (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#2A2417] border border-[#4A3D22] text-[12px] text-[#D8B16C] font-mono" title="Ambiguous network outcome on prior dispatch. Duplicate retries locked.">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Uncertain Delivery</span>
                  </div>
                ) : (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleOpenSendModal}
                    leftIcon={<Mail className="w-4 h-4" />}
                    disabled={!isSenderConfigured || !recipient.trim()}
                    title={
                      !isSenderConfigured
                        ? 'Configure Google OAuth or SMTP in Integrations before sending'
                        : !recipient.trim()
                        ? 'Add recipient email before sending'
                        : `Review and confirm email dispatch via ${activeProviderName}`
                    }
                  >
                    Send Email
                  </Button>
                )}
              </>
            )}
          </div>
        </div>


        {/* Draft Tabs & Filter Bar */}
        <div className="flex items-center justify-between gap-3 pt-1 border-t border-[#1E2126]">
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar flex-1">
            <span className="text-[11px] text-[#727780] mr-1 shrink-0">Saved drafts:</span>
            {filteredDrafts.map((d) => {
              const p = prospects.find((pr) => pr.id === d.prospectId);
              const isActive = activeDraft?.id === d.id;
              return (
                <button
                  key={d.id}
                  onClick={() => setActiveDraftId(d.id)}
                  className={`flex items-center gap-2 px-3 py-1 rounded text-[12px] font-medium transition-colors shrink-0 ${
                    isActive
                      ? 'bg-[#24272C] text-[#F3F4F6] border border-[#3E4550]'
                      : 'bg-[#17191C] text-[#727780] hover:text-[#A0A5AD] border border-[#26292F]'
                  }`}
                >
                  <Mail className="w-3.5 h-3.5 text-[#A0A5AD]" />
                  <span className="truncate max-w-[140px]">{p?.name || 'Draft'}</span>
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    d.status === 'approved' ? 'bg-[#80B89A]' :
                    d.status === 'edited' ? 'bg-[#91B7D8]' : 'bg-[#D8B16C]'
                  }`} />
                </button>
              );
            })}
            {filteredDrafts.length === 0 && (
              <span className="text-[11px] text-[#727780] italic">No drafts matching filter</span>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#17191C] border border-[#2B2F36] rounded px-2.5 py-1 text-[11px] text-[#A0A5AD] outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="edited">Edited</option>
              <option value="approved">Approved</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {activeDraft ? (
        <div className="flex-1 overflow-hidden p-6 flex flex-col lg:flex-row gap-6">
          {/* Main Column: Email Composer */}
          <div className="flex-1 flex flex-col rounded border border-[#282B31] bg-[#17191C] overflow-hidden">
            <div className="px-5 py-3 border-b border-[#24272D] flex items-center justify-between bg-[#1D2024]/50">
              <div className="flex items-center gap-2">
                <span className="text-[12px] font-medium text-[#F3F4F6]">
                  {isPreviewMode ? 'Live Outreach Preview' : 'Outreach Message Body'}
                </span>
                {isDirty && (
                  <span className="text-[10px] text-[#D8B16C] bg-[#2A2417] px-1.5 py-0.2 rounded border border-[#4A3D22]">
                    Unsaved Edits
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleCopySubject}
                  title="Copy subject line"
                  className="p-1 rounded text-[#727780] hover:text-[#F3F4F6] text-[11px] flex items-center gap-1 transition-colors"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>Subject</span>
                </button>
                <button
                  onClick={handleCopyBody}
                  title="Copy email body"
                  className="p-1 rounded text-[#727780] hover:text-[#F3F4F6] text-[11px] flex items-center gap-1 transition-colors"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>Body</span>
                </button>
                <span className="text-[#363B44]">|</span>
                <button
                  onClick={() => setIsRegenerateModalOpen(true)}
                  className="p-1 rounded text-[#727780] hover:text-[#D8E7A2] text-[11px] flex items-center gap-1 transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Regenerate</span>
                </button>
                <button
                  onClick={() => setIsDeleteModalOpen(true)}
                  className="p-1 rounded text-[#727780] hover:text-[#D78383] text-[11px] flex items-center gap-1 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete</span>
                </button>
                <span className="text-[#363B44]">|</span>
                <div className="flex items-center gap-1.5 text-[11px] text-[#727780]">
                  <span>Status:</span>
                  <span className={`font-mono px-1.5 py-0.5 rounded border text-[10px] ${
                    activeDraft.status === 'approved' || activeDraft.status === 'submitted'
                      ? 'bg-[#18261F] text-[#80B89A] border-[#253D30]'
                      : activeDraft.status === 'uncertain'
                      ? 'bg-[#2A2417] text-[#D8B16C] border-[#4A3D22]'
                      : activeDraft.status === 'edited'
                      ? 'bg-[#1D2530] text-[#91B7D8] border-[#2B3A4F]'
                      : 'bg-[#22271B] text-[#D8E7A2] border-[#364024]'
                  }`}>
                    {activeDraft.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
              {/* Recipient */}
              <div className="flex flex-col gap-2 border-b border-[#24272D] pb-3">
                <div className="flex items-center gap-3">
                  <label className="w-20 text-[12px] font-medium text-[#727780]">Recipient:</label>
                  <input
                    type="email"
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    placeholder="Enter verified business email (e.g. info@domain.com)"
                    className="flex-1 bg-transparent text-[13px] font-mono text-[#F3F4F6] outline-none placeholder:text-[#4A505C]"
                  />
                  {recipient.trim() ? (
                    <span className="font-mono text-[10px] bg-[#18261F] text-[#80B89A] border border-[#253D30] px-2 py-0.5 rounded flex items-center gap-1 shrink-0">
                      <CheckCircle2 className="w-3 h-3" /> Ready
                    </span>
                  ) : (
                    <span className="font-mono text-[10px] bg-[#2A2417] text-[#D8B16C] border border-[#4A3D22] px-2 py-0.5 rounded flex items-center gap-1 shrink-0">
                      <AlertTriangle className="w-3 h-3" /> Unverified / Missing
                    </span>
                  )}
                </div>

                {/* Quick suggestions if domain is available and recipient is empty */}
                {suggestedDomain && !recipient.trim() && (
                  <div className="flex items-center gap-2 text-[11px] text-[#727780] pl-23 flex-wrap">
                    <span>Quick fill:</span>
                    <button
                      type="button"
                      onClick={() => setRecipient(`info@${suggestedDomain}`)}
                      className="font-mono text-[10px] text-[#91B7D8] hover:text-[#F3F4F6] bg-[#171E28] hover:bg-[#202936] border border-[#2B3A4F] px-2 py-0.5 rounded transition-colors"
                      title={`Fill with info@${suggestedDomain}`}
                    >
                      + info@{suggestedDomain}
                    </button>
                    <button
                      type="button"
                      onClick={() => setRecipient(`contact@${suggestedDomain}`)}
                      className="font-mono text-[10px] text-[#91B7D8] hover:text-[#F3F4F6] bg-[#171E28] hover:bg-[#202936] border border-[#2B3A4F] px-2 py-0.5 rounded transition-colors"
                      title={`Fill with contact@${suggestedDomain}`}
                    >
                      + contact@{suggestedDomain}
                    </button>
                  </div>
                )}

                {/* Solution A: Compact Integrity Callout & Real Phone Actions when recipient is empty */}
                {!recipient.trim() && (
                  <div className="mt-1 p-3 rounded-lg bg-[#211B10] border border-[#4A3816] flex flex-col md:flex-row md:items-center justify-between gap-3 text-[12px]">
                    <div className="flex items-start md:items-center gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 md:mt-0 text-[#D8B16C]" />
                      <div className="flex flex-col gap-0.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <strong className="text-[#F5CF87] font-medium text-[12px]">
                            No verified email on file for {associatedProspect?.name || 'this prospect'}
                          </strong>
                          {realPhone && (
                            <span className="text-[11px] text-[#A0A5AD] font-mono">
                              · Phone: <strong className="text-[#F3F4F6]">{realPhone}</strong>
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[#C2A36B]">
                          Reach out directly via phone or WhatsApp, enter email above, or run automated crawlers:
                        </p>
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-1.5 shrink-0 flex-wrap">
                      {realPhone && (
                        <>
                          {telLink && (
                            <a
                              href={telLink}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#1D2530] text-[#91B7D8] hover:bg-[#253242] border border-[#2B3A4F] text-[11px] font-mono transition-colors"
                              title="Call business phone"
                            >
                              <Phone className="w-3 h-3" />
                              <span>Call</span>
                            </a>
                          )}
                          {waPitchLink && (
                            <a
                              href={waPitchLink}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#18261F] text-[#80B89A] hover:bg-[#1F3329] border border-[#253D30] text-[11px] font-mono transition-colors"
                              title="Open WhatsApp chat with prefilled audit letter"
                            >
                              <MessageSquare className="w-3 h-3" />
                              <span>WhatsApp</span>
                            </a>
                          )}
                        </>
                      )}

                      {associatedProspect?.websiteUrl && (
                        <Button
                          variant="secondary"
                          size="sm"
                          isLoading={isExtractingContacts}
                          onClick={handleExtractFromWebsite}
                          leftIcon={<Globe className="w-3.5 h-3.5 text-[#91B7D8]" />}
                          title={`Crawl ${associatedProspect.websiteUrl} for published emails`}
                        >
                          Scrape
                        </Button>
                      )}

                      <Button
                        variant="secondary"
                        size="sm"
                        isLoading={isExtractingContacts}
                        onClick={handleFindViaHunter}
                        leftIcon={<Search className="w-3.5 h-3.5 text-[#D8E7A2]" />}
                        title="Search corporate email directory via Hunter.io"
                      >
                        Hunter.io
                      </Button>
                    </div>
                  </div>
                )}
              </div>

              {/* Subject */}
              <div className="flex flex-col gap-2 border-b border-[#24272D] pb-3">
                <div className="flex items-center gap-3">
                  <label className="w-20 text-[12px] font-medium text-[#727780]">Subject:</label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Subject line"
                    className="flex-1 bg-transparent text-[13px] font-medium text-[#F3F4F6] outline-none"
                  />
                </div>

                {/* Subject Alternative Suggestions */}
                {activeDraft?.subjectAlternatives && activeDraft.subjectAlternatives.length > 0 && (
                  <div className="flex items-center gap-2 ml-23 text-[11px] text-[#727780] overflow-x-auto no-scrollbar">
                    <span>Alternates:</span>
                    {activeDraft.subjectAlternatives.map((alt, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSubject(alt)}
                        className="px-2 py-0.5 rounded bg-[#111214] border border-[#2B2F36] hover:border-[#3E4550] text-[#A0A5AD] hover:text-[#F3F4F6] whitespace-nowrap transition-colors"
                      >
                        {alt}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Email Body */}
              {isPreviewMode ? (
                <div className="w-full min-h-[340px] p-4 rounded-lg bg-[#111214] border border-[#24272D] text-[13px] text-[#D6D9E0] whitespace-pre-wrap font-sans leading-relaxed overflow-y-auto">
                  {body}
                </div>
              ) : (
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={15}
                  className="w-full min-h-[340px] bg-[#111214] border border-[#24272D] rounded-lg p-4 text-[13px] text-[#F3F4F6] font-sans leading-relaxed focus:border-[#3E4550] outline-none overflow-y-auto resize-y"
                  placeholder="Compose outreach message..."
                />
              )}

              {/* Notice Banner */}
              <div className="p-3 rounded bg-[#141619] border border-[#24272D] flex items-center justify-between text-[11px] text-[#727780]">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#80B89A]" />
                  <span>
                    {activeDraft?.status === 'submitted' && activeDraft?.providerMessageId
                      ? `Dispatched via Gmail API (Message ID: ${activeDraft.providerMessageId}). Retries blocked.`
                      : 'Phase 6 Active: Individual dispatch strictly through authenticated Gmail API with explicit confirmation. Bulk sending is disabled.'}
                  </span>
                </div>
                <span className="font-mono text-[#80B89A]">
                  {activeDraft?.status === 'submitted' ? 'Dispatched' : 'Explicit Approval'}
                </span>
              </div>

            </div>
          </div>

          {/* Right Column: Verified Audit Findings & AI Claim Rationale */}
          <div className="w-full lg:w-96 shrink-0 flex flex-col gap-4 overflow-y-auto">
            {/* Target Prospect Card */}
            {associatedProspect && (
              <div className="rounded border border-[#2B2F36] bg-[#17191C] p-4 flex flex-col gap-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-medium text-[#727780] uppercase tracking-wider">
                    Target Entity
                  </span>
                  <button
                    onClick={handleOpenProspect}
                    className="text-[11px] text-[#D8E7A2] hover:underline flex items-center gap-1"
                  >
                    <span>Inspect Prospect</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-[#A0A5AD]" />
                  <span className="font-medium text-[#F3F4F6] text-[13px]">{associatedProspect.name}</span>
                </div>
                <div className="text-[12px] text-[#727780]">
                  {associatedProspect.category} · {associatedProspect.location.city}
                </div>
                <div className="text-[11px] font-mono text-[#91B7D8] flex items-center gap-1">
                  <Globe className="w-3 h-3 text-[#727780]" />
                  <span>{associatedProspect.websiteUrl || 'No domain listed'}</span>
                </div>

                {/* Direct Verified Phone Actions */}
                <div className="pt-2 border-t border-[#24272D] flex flex-col gap-1.5 text-[11px]">
                  <div className="flex items-center justify-between">
                    <span className="text-[#727780] flex items-center gap-1">
                      <Phone className="w-3 h-3 text-[#A0A5AD]" />
                      <span>Phone:</span>
                    </span>
                    {associatedProspect.phone ? (
                      <span className="font-mono text-[#F3F4F6] font-medium">{associatedProspect.phone}</span>
                    ) : (
                      <span className="text-[#727780] italic">Not on file</span>
                    )}
                  </div>
                  {associatedProspect.phone && (
                    <div className="flex items-center gap-1.5 justify-end mt-0.5">
                      <a
                        href={`tel:${associatedProspect.phone.replace(/[^0-9+]/g, '')}`}
                        className="px-2 py-0.5 rounded bg-[#1D2530] text-[#91B7D8] hover:bg-[#253242] border border-[#2B3A4F] text-[10px] font-mono transition-colors"
                        title="Call business phone"
                      >
                        Call
                      </a>
                      <a
                        href={`https://wa.me/${associatedProspect.phone.replace(/[^0-9]/g, '')}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2 py-0.5 rounded bg-[#18261F] text-[#80B89A] hover:bg-[#1F3329] border border-[#253D30] text-[10px] font-mono transition-colors"
                        title="Chat on WhatsApp"
                      >
                        WhatsApp
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* AI Generation Details */}
            <div className="rounded border border-[#2B2F36] bg-[#17191C] p-4 flex flex-col gap-2.5 text-[11px]">
              <span className="font-medium text-[#727780] uppercase tracking-wider">
                Generation Provenance
              </span>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">AI Provider:</span>
                <span className="font-mono text-[#F3F4F6]">{activeDraft.aiProvider || 'openai'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Model:</span>
                <span className="font-mono text-[#A0A5AD]">{activeDraft.aiModel || 'gpt-4o-mini'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Outreach Purpose:</span>
                <span className="font-mono text-[#D8E7A2]">{activeDraft.outreachPurpose || 'website_improvement'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Tone:</span>
                <span className="font-mono text-[#A0A5AD]">{activeDraft.writingTone || 'professional'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#727780]">Created:</span>
                <span className="font-mono text-[#727780]">{activeDraft.createdAt}</span>
              </div>
            </div>

            {/* Why the AI Included Specific Claims in this Message */}
            <div className="rounded border border-[#2B2F36] bg-[#17191C] p-4 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-[12px] font-medium text-[#F3F4F6]">
                  <FileText className="w-3.5 h-3.5 text-[#D8E7A2]" />
                  <span>Verified Claim Citations</span>
                </div>
                <span className="text-[11px] font-mono text-[#80B89A]">Deterministic</span>
              </div>

              <p className="text-[11px] text-[#727780] leading-relaxed">
                Every technical assertion in the draft is validated against authentic crawler evidence.
              </p>

              <div className="flex flex-col gap-2">
                {activeDraft.aiClaimsRationale && activeDraft.aiClaimsRationale.length > 0 ? (
                  activeDraft.aiClaimsRationale.map((cr, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1 text-[12px]"
                    >
                      <div className="font-medium text-[#F3F4F6] flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          cr.evidenceType === 'none' ? 'bg-[#D78383]' : 'bg-[#D8E7A2]'
                        }`} />
                        <span>{cr.claim}</span>
                      </div>
                      <div className="text-[11px] text-[#A0A5AD] leading-relaxed font-mono mt-0.5">
                        {cr.rationale}
                      </div>
                      {cr.findingId && cr.findingId !== 'general' && (
                        <div className="text-[10px] text-[#727780] font-mono">
                          Citation ID: {cr.findingId}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-[12px] text-[#727780] italic">
                    General introductory proposal without technical citations.
                  </div>
                )}
              </div>
            </div>

            {/* Associated Audit Findings Quick Reference */}
            {associatedAudit && (
              <div className="rounded border border-[#2B2F36] bg-[#17191C] p-4 flex flex-col gap-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-medium text-[#727780] uppercase tracking-wider">
                    Dossier Findings Reference
                  </span>
                  <span className="text-[11px] font-mono text-[#727780]">{associatedAudit.findings.length} findings</span>
                </div>

                <div className="flex flex-col gap-1.5 max-h-56 overflow-y-auto">
                  {associatedAudit.findings.map((f) => {
                    const isCited = activeDraft.findingsReferenced?.includes(f.id);
                    return (
                      <div
                        key={f.id}
                        className={`p-2 rounded border flex items-center justify-between text-[11px] ${
                          isCited
                            ? 'bg-[#1D2018] border-[#3E4929]'
                            : 'bg-[#111214] border-[#24272D]'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 truncate pr-2">
                          {isCited && <span className="w-1.5 h-1.5 rounded-full bg-[#D8E7A2] shrink-0" />}
                          <span className={`truncate ${isCited ? 'text-[#F3F4F6] font-medium' : 'text-[#A0A5AD]'}`}>
                            {f.title}
                          </span>
                        </div>
                        <Badge variant="severity" severity={f.severity} size="sm" />
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Empty State */
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[#1D2024] border border-[#2B2F36] flex items-center justify-center text-[#727780]">
            <Mail className="w-6 h-6" />
          </div>
          <div className="flex flex-col gap-1 max-w-sm">
            <h2 className="text-[16px] font-semibold text-[#F3F4F6]">No Saved Outreach Drafts</h2>
            <p className="text-[12px] text-[#A0A5AD]">
              Select any prospect from your pipeline or discovery results to generate a personalized, evidence-backed email draft.
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={() => setIsGenerateModalOpen(true)}
            leftIcon={<Sparkles className="w-4 h-4" />}
          >
            Generate First Draft
          </Button>
        </div>
      )}

      {/* Regenerate Confirmation & Parameter Modal */}
      {isRegenerateModalOpen && activeDraft && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="w-full max-w-md rounded border border-[#30343A] bg-[#17191C] shadow-2xl p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-[#24272D] pb-3">
              <div className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-[#D8E7A2]" />
                <h3 className="text-[14px] font-medium text-[#F3F4F6]">Regenerate Email Draft</h3>
              </div>
              <button onClick={() => setIsRegenerateModalOpen(false)} className="text-[#727780] hover:text-[#F3F4F6]">
                <X className="w-4 h-4" />
              </button>
            </div>

            {isDirty && (
              <div className="p-2.5 rounded bg-[#2A2417] border border-[#4A3D22] text-[12px] text-[#D8B16C] flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  <strong>Warning:</strong> You have unsaved edits in your current draft. Regenerating will replace your current subject and body with fresh model output.
                </span>
              </div>
            )}

            <div className="flex flex-col gap-3 text-[12px]">
              <div>
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Outreach Purpose
                </label>
                <select
                  value={regenPurpose}
                  onChange={(e) => setRegenPurpose(e.target.value)}
                  className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[12px] text-[#F3F4F6] outline-none"
                >
                  <option value="website_improvement">Website Improvement</option>
                  <option value="website_redesign">Website Redesign</option>
                  <option value="new_website_proposal">New Website Proposal</option>
                  <option value="website_maintenance">Website Maintenance</option>
                  <option value="general_introduction">General Introduction</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Writing Tone
                </label>
                <select
                  value={regenTone}
                  onChange={(e) => setRegenTone(e.target.value)}
                  className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[12px] text-[#F3F4F6] outline-none"
                >
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="concise">Concise</option>
                  <option value="consultative">Consultative</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Updated Instructions <span className="text-[#727780] lowercase">(optional)</span>
                </label>
                <textarea
                  value={regenInstructions}
                  onChange={(e) => setRegenInstructions(e.target.value.slice(0, 500))}
                  placeholder="e.g. Focus exclusively on the TLS certificate issue."
                  rows={2}
                  className="w-full bg-[#111214] border border-[#30343A] rounded p-2 text-[12px] text-[#F3F4F6] outline-none resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[#24272D]">
              <Button variant="ghost" size="md" onClick={() => setIsRegenerateModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="md"
                isLoading={isRegenerating}
                onClick={handleConfirmRegenerate}
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                Regenerate Draft
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Draft Confirmation Modal */}
      {isDeleteModalOpen && activeDraft && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="w-full max-w-sm rounded border border-[#30343A] bg-[#17191C] shadow-2xl p-5 flex flex-col gap-4">
            <div className="flex items-center gap-2 text-[#D78383]">
              <Trash2 className="w-5 h-5" />
              <h3 className="text-[14px] font-medium text-[#F3F4F6]">Delete Email Draft</h3>
            </div>
            <p className="text-[12px] text-[#A0A5AD] leading-relaxed">
              Are you sure you want to permanently delete this draft for <strong>{associatedProspect?.name || 'this prospect'}</strong>? This operation removes the draft from SQLite.
            </p>
            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[#24272D]">
              <Button variant="ghost" size="md" onClick={() => setIsDeleteModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="md"
                onClick={handleConfirmDelete}
                leftIcon={<Trash2 className="w-4 h-4" />}
              >
                Delete Draft
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Explicit Send Confirmation Modal */}
      {isSendModalOpen && activeDraft && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="w-full max-w-2xl rounded border border-[#30343A] bg-[#17191C] shadow-2xl p-6 flex flex-col gap-4 max-h-[90vh] overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#24272D] pb-3">
              <div className="flex items-center gap-2.5">
                <Mail className="w-5 h-5 text-[#80B89A]" />
                <h3 className="text-[16px] font-semibold text-[#F3F4F6] tracking-tight">
                  Explicit Send Authorization
                </h3>
              </div>
              <button
                onClick={() => setIsSendModalOpen(false)}
                className="text-[#727780] hover:text-[#F3F4F6] transition-colors"
                disabled={isSending}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Success State */}
            {sendResult?.success ? (
              <div className="p-4 rounded bg-[#16211B] border border-[#2D4536] flex flex-col gap-3 text-[13px] text-[#80B89A]">
                <div className="flex items-center gap-2 font-medium">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Outreach proposal accepted by {sendResult.provider || activeProviderName}</span>
                </div>
                <div className="text-[12px] text-[#A0A5AD] flex flex-col gap-1">
                  <span>Message ID: <strong className="font-mono text-[#F3F4F6]">{sendResult.messageId}</strong></span>
                  <span>Draft status updated to <strong>Submitted</strong> and recorded in Dispatch History. Retries are now locked.</span>
                  <span className="text-[11px] text-[#727780] italic">Accepted by mail server gateway for transmission; inbox delivery depends on recipient mail policies.</span>
                </div>
                <div className="flex justify-end pt-2">
                  <Button variant="primary" size="md" onClick={() => setIsSendModalOpen(false)}>
                    Done
                  </Button>
                </div>
              </div>
            ) : (
              <>
                {sendResult?.error && (
                  <div className={`p-3.5 rounded border text-[12px] flex items-start gap-2.5 ${
                    sendResult.error.toLowerCase().includes('uncertain')
                      ? 'bg-[#2A2417] border-[#4A3D22] text-[#D8B16C]'
                      : 'bg-[#2A1818] border-[#4A2626] text-[#D78383]'
                  }`}>
                    {sendResult.error.toLowerCase().includes('uncertain') ? (
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    )}
                    <div>
                      {sendResult.error.toLowerCase().includes('uncertain') && (
                        <div className="font-medium text-[#F3F4F6] mb-0.5">Uncertain Delivery State</div>
                      )}
                      <span>{sendResult.error}</span>
                    </div>
                  </div>
                )}

                <div className="flex-1 overflow-y-auto flex flex-col gap-3 text-[12px]">
                  {/* Transmission Summary Box */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-3 rounded bg-[#131518] border border-[#262A30] flex flex-col gap-1">
                      <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">FROM (Sender Account)</span>
                      <span className="font-mono text-[13px] text-[#80B89A] flex items-center gap-1.5 truncate">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#80B89A]" />
                        {activeSenderEmail}
                      </span>
                    </div>

                    <div className="p-3 rounded bg-[#131518] border border-[#262A30] flex flex-col gap-1">
                      <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">PROVIDER</span>
                      <span className="font-mono text-[13px] text-[#D8E7A2] flex items-center gap-1.5 truncate">
                        {activeProviderName}
                      </span>
                    </div>

                    <div className="p-3 rounded bg-[#131518] border border-[#262A30] flex flex-col gap-1">
                      <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">TO (Target Recipient)</span>
                      <span className="font-mono text-[13px] text-[#F3F4F6] truncate">
                        {recipient}
                      </span>
                    </div>
                  </div>

                  {/* Subject Line */}
                  <div className="p-3 rounded bg-[#131518] border border-[#262A30] flex flex-col gap-1">
                    <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">SUBJECT</span>
                    <span className="font-medium text-[13px] text-[#F3F4F6]">
                      {subject}
                    </span>
                  </div>

                  {/* Exact Body Preview */}
                  <div className="flex flex-col gap-1">
                    <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">FINAL EMAIL BODY</span>
                    <div className="p-3.5 rounded bg-[#111214] border border-[#262A30] text-[12px] text-[#D6D9E0] font-sans leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                      {body}
                    </div>
                  </div>

                  {/* Spam and Privacy Safeguards Notice */}
                  <div className="p-3 rounded bg-[#14181E] border border-[#232F42] flex items-start gap-2.5 text-[11px] text-[#91B7D8]">
                    <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5 text-[#91B7D8]" />
                    <p className="leading-relaxed">
                      <strong>Responsible Sending Policy:</strong> Leddro sends individual, explicitly confirmed client proposals anchored in verified technical website observations. Mass emailing, automatic sequences, and uninspected retries are strictly prohibited.
                    </p>
                  </div>

                  {/* Explicit Confirmation Checkbox */}
                  <label className="flex items-start gap-3 p-3 rounded bg-[#191D16] border border-[#3E4929] cursor-pointer hover:bg-[#1E241B] transition-colors select-none">
                    <input
                      type="checkbox"
                      id="confirm-explicit-send"
                      checked={explicitConfirm}
                      onChange={(e) => setExplicitConfirm(e.target.checked)}
                      className="mt-0.5 w-4 h-4 rounded border-[#30343A] bg-[#17191C] text-[#D8E7A2] focus:ring-0"
                    />
                    <div className="text-[12px] text-[#F3F4F6]">
                      <span className="font-medium">I explicitly authorize sending this proposal.</span>
                      <p className="text-[11px] text-[#A0A5AD] mt-0.5">
                        I have verified the recipient address, subject, and content. I confirm dispatch via {activeProviderName} from {activeSenderEmail}.
                      </p>
                    </div>
                  </label>
                </div>

                {/* Modal Actions */}
                <div className="flex items-center justify-between pt-3 border-t border-[#24272D]">
                  <Button variant="ghost" size="md" onClick={() => setIsSendModalOpen(false)} disabled={isSending}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    size="md"
                    isLoading={isSending}
                    disabled={!explicitConfirm || isSending}
                    onClick={handleExecuteSend}
                    leftIcon={<Mail className="w-4 h-4" />}
                  >
                    Authorize &amp; Send via {isSMTP ? 'Gmail SMTP' : 'Gmail API'}
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Generate Draft Modal */}
      <GenerateDraftModal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        targetProspectId={associatedProspect?.id}
      />
    </div>

  );
};
