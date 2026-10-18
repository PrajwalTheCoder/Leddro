import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Sparkles, 
  X, 
  ShieldCheck, 
  AlertCircle, 
  Building2, 
  CheckCircle2, 
  Cpu, 
  FileText, 
  ExternalLink,
  ChevronRight,
  RefreshCw,
  Info
} from 'lucide-react';
import { Button } from './Button';
import { Badge } from './Badge';
import { useApp } from '../../context/AppContext';
import { Prospect, AuditReport, AIProviderStatus } from '../../types';

interface GenerateDraftModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetProspectId?: string | null;
  targetAuditId?: string | null;
}

export const GenerateDraftModal: React.FC<GenerateDraftModalProps> = ({
  isOpen,
  onClose,
  targetProspectId,
  targetAuditId
}) => {
  const { prospects, auditReports, addToast, setActiveDraftId, refreshProspects } = useApp();
  const navigate = useNavigate();

  // Selection state
  const [selectedProspectId, setSelectedProspectId] = useState<string>(targetProspectId || '');
  const [purpose, setPurpose] = useState<'website_improvement' | 'website_redesign' | 'new_website_proposal' | 'website_maintenance' | 'general_introduction'>('website_improvement');
  const [tone, setTone] = useState<'professional' | 'friendly' | 'concise' | 'consultative'>('professional');
  const [customInstructions, setCustomInstructions] = useState('');
  const [privacyConsent, setPrivacyConsent] = useState(false);

  // AI Providers state
  const [providers, setProviders] = useState<AIProviderStatus[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string>('');
  const [isLoadingProviders, setIsLoadingProviders] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);

  // Sync target prospect when opened
  useEffect(() => {
    if (targetProspectId) {
      setSelectedProspectId(targetProspectId);
    } else if (prospects.length > 0 && !selectedProspectId) {
      setSelectedProspectId(prospects[0].id);
    }
  }, [targetProspectId, prospects]);

  // Fetch AI providers status on mount/open
  useEffect(() => {
    if (isOpen) {
      setIsLoadingProviders(true);
      fetch('/api/ai/providers')
        .then((res) => (res.ok ? res.json() : []))
        .then((data: AIProviderStatus[]) => {
          setProviders(data);
          // Prefer active configured provider, else first configured (e.g. Gemini), else active, else first in list
          const activeConfigured = data.find((p) => p.is_active && p.is_configured);
          const firstConfigured = data.find((p) => p.is_configured);
          const active = data.find((p) => p.is_active);
          const preferred = activeConfigured || firstConfigured || active || data[0];
          if (preferred) {
            setSelectedProviderId(preferred.provider_id);
          }
        })
        .catch(() => {})
        .finally(() => setIsLoadingProviders(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const currentProspect = prospects.find((p) => p.id === selectedProspectId) || prospects[0];
  const activeProvider = (selectedProviderId ? providers.find((p) => p.provider_id === selectedProviderId) : null) ||
                         providers.find((p) => p.is_active && p.is_configured) ||
                         providers.find((p) => p.is_configured) ||
                         providers.find((p) => p.is_active) || 
                         providers[0];
  const isProviderConfigured = activeProvider ? activeProvider.is_configured : false;

  // Resolve audit report
  const resolvedAuditId = targetAuditId || currentProspect?.latestAuditId;
  const auditReport: AuditReport | undefined = resolvedAuditId ? auditReports[resolvedAuditId] : undefined;

  const handleGenerate = async () => {
    if (!currentProspect) {
      addToast('Please select a target prospect.', 'warning');
      return;
    }

    if (!isProviderConfigured) {
      addToast('No AI provider is configured. Configure your API key or local Ollama first.', 'error');
      return;
    }

    if (!privacyConsent) {
      addToast('Explicit privacy consent is required before transmitting prospect data to the AI provider.', 'warning');
      return;
    }

    setIsGenerating(true);
    setGenerationError(null);

    try {
      const response = await fetch('/api/drafts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prospect_id: currentProspect.id,
          audit_id: auditReport?.id,
          purpose,
          tone,
          custom_instructions: customInstructions.trim() || undefined,
          privacy_consent: true,
          provider_override: activeProvider?.provider_id
        })
      });

      if (!response.ok) {
        let errMessage = `Generation failed (HTTP ${response.status})`;
        try {
          const errData = await response.json();
          if (errData.detail) errMessage = errData.detail;
        } catch {
          // ignore
        }
        throw new Error(errMessage);
      }

      const newDraft = await response.json();
      addToast(`Personalized email draft created for ${currentProspect.name}`, 'success');

      // Refresh prospects to update status
      await refreshProspects();

      // Set active draft and navigate
      setActiveDraftId(newDraft.id);
      onClose();
      navigate('/drafts');
    } catch (err: any) {
      setGenerationError(err.message || 'An unexpected error occurred during AI generation.');
      addToast(`Draft generation failed: ${err.message}`, 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="w-full max-w-2xl rounded border border-[#30343A] bg-[#17191C] shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#24272D] flex items-center justify-between bg-[#1A1C20]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-[#22271B] border border-[#364024] flex items-center justify-center text-[#D8E7A2]">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-[15px] font-semibold text-[#F3F4F6] tracking-tight">
                AI Evidence-Based Outreach Generation
              </h2>
              <p className="text-[11px] text-[#A0A5AD]">
                Formulates a personalized, honest outreach letter anchored in deterministic findings.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isGenerating}
            className="text-[#727780] hover:text-[#F3F4F6] transition-colors disabled:opacity-40"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 flex flex-col gap-4 text-[12px]">
          {/* Target Prospect Selection / Summary */}
          <div className="rounded border border-[#2B2F36] bg-[#141618] p-3.5 flex flex-col gap-2">
            <div className="flex items-center justify-between text-[11px] text-[#727780] uppercase tracking-wider font-medium">
              <span>Target Prospect</span>
              {currentProspect && (
                <span className="font-mono text-[#D8E7A2] bg-[#22271B] px-1.5 py-0.5 rounded border border-[#364024]">
                  Opportunity Score: {currentProspect.opportunityScore}/100
                </span>
              )}
            </div>

            {prospects.length > 1 && !targetProspectId ? (
              <select
                value={selectedProspectId}
                onChange={(e) => setSelectedProspectId(e.target.value)}
                disabled={isGenerating}
                className="bg-[#1A1C20] border border-[#30343A] rounded px-3 py-1.5 text-[12px] text-[#F3F4F6] outline-none"
              >
                {prospects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.category} · {p.location.city})
                  </option>
                ))}
              </select>
            ) : currentProspect ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-[#A0A5AD]" />
                  <span className="font-medium text-[#F3F4F6] text-[13px]">{currentProspect.name}</span>
                  <span className="text-[11px] text-[#727780]">({currentProspect.category} · {currentProspect.location.city})</span>
                </div>
                <Badge variant="website" websiteStatus={currentProspect.websiteStatus} size="sm" />
              </div>
            ) : null}

            {/* Audit Status Quick Pill */}
            {auditReport ? (
              <div className="flex items-center justify-between pt-1 border-t border-[#22252A] text-[11px] font-mono text-[#A0A5AD]">
                <span>Attached Audit: <strong className="text-[#F3F4F6]">{auditReport.findings.length} findings</strong> recorded</span>
                <span className="text-[#80B89A]">Score: {auditReport.overallScore}/100</span>
              </div>
            ) : (
              <div className="text-[11px] text-[#A0A5AD] pt-1 border-t border-[#22252A] italic">
                No website audit report available. Draft will be based on verified business details and general proposal.
              </div>
            )}
          </div>

          {/* Outreach Configuration (Purpose & Tone) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1.5">
                Outreach Purpose
              </label>
              <select
                value={purpose}
                onChange={(e) => setPurpose(e.target.value as any)}
                disabled={isGenerating}
                className="w-full bg-[#141618] border border-[#30343A] rounded px-3 py-2 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
              >
                <option value="website_improvement">Website Improvement (Focus on verified issues)</option>
                <option value="website_redesign">Website Redesign (Modernization proposal)</option>
                <option value="new_website_proposal">New Website Proposal (Inquire on web presence)</option>
                <option value="website_maintenance">Website Maintenance (Ongoing patching &amp; upkeep)</option>
                <option value="general_introduction">General Introduction (Introductory capabilities)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1.5">
                Writing Tone
              </label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value as any)}
                disabled={isGenerating}
                className="w-full bg-[#141618] border border-[#30343A] rounded px-3 py-2 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
              >
                <option value="professional">Professional (Authoritative &amp; measured)</option>
                <option value="friendly">Friendly (Approachable &amp; warm)</option>
                <option value="concise">Concise (Direct, under 100 words)</option>
                <option value="consultative">Consultative (Analytical &amp; advisory)</option>
              </select>
            </div>
          </div>

          {/* Optional Instructions */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider">
                Custom Operator Guidance <span className="text-[#727780] lowercase font-normal">(optional, max 500 chars)</span>
              </label>
              <span className="font-mono text-[10px] text-[#727780]">{customInstructions.length}/500</span>
            </div>
            <textarea
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value.slice(0, 500))}
              disabled={isGenerating}
              placeholder="e.g., Emphasize our experience with industrial manufacturers in Maharashtra; keep opening brief."
              rows={2}
              className="w-full bg-[#141618] border border-[#30343A] rounded p-2.5 text-[12px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none resize-none"
            />
          </div>

          {/* Selected Provider Badge & Status Notice */}
          <div className="rounded border border-[#2B2F36] bg-[#141618] p-3 flex flex-col gap-2.5">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-[#D8E7A2]" />
                <span className="text-[12px] font-medium text-[#F3F4F6]">
                  Active AI Engine:
                </span>
                {providers.length > 0 ? (
                  <select
                    value={activeProvider?.provider_id || selectedProviderId}
                    onChange={(e) => setSelectedProviderId(e.target.value)}
                    disabled={isGenerating}
                    className="bg-[#1C212D] border border-[#30343A] rounded px-2.5 py-1 text-[11px] text-[#F3F4F6] focus:border-[#D8E7A2] outline-none font-mono cursor-pointer"
                  >
                    {providers.map((p) => (
                      <option key={p.provider_id} value={p.provider_id}>
                        {p.name} {p.is_configured ? '• Ready' : '• Missing Config'}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className="text-[12px] text-[#A0A5AD]">Checking...</span>
                )}
              </div>
              <span className={`font-mono text-[11px] px-2 py-0.5 rounded border shrink-0 ${
                isProviderConfigured
                  ? 'bg-[#18261F] text-[#80B89A] border-[#253D30]'
                  : 'bg-[#2A1818] text-[#D78383] border-[#4A2626]'
              }`}>
                {isProviderConfigured ? `Ready (${activeProvider?.current_model})` : 'Missing Configuration'}
              </span>
            </div>

            {!isProviderConfigured ? (
              <div className="p-2.5 rounded bg-[#2A1818] border border-[#4A2626] text-[11px] text-[#D78383] flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="flex flex-col gap-1.5 flex-1">
                  <span><strong>AI Provider Not Configured:</strong> {activeProvider?.status_message || 'Please configure an AI provider in your .env file or Integrations.'}</span>
                  <div className="text-[#A0A5AD]">
                    Add your API key (GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY) in the <code className="text-[#F3F4F6]">.env</code> file, or run a local Ollama instance (<code className="text-[#F3F4F6]">ollama run llama3</code>).
                  </div>
                  {providers.some((p) => p.is_configured) && (
                    <div className="pt-0.5">
                      <button
                        type="button"
                        onClick={() => {
                          const configured = providers.find((p) => p.is_configured);
                          if (configured) setSelectedProviderId(configured.provider_id);
                        }}
                        className="px-2.5 py-1 rounded bg-[#18261F] border border-[#253D30] text-[#80B89A] hover:bg-[#20332a] text-[11px] font-medium transition-colors cursor-pointer"
                      >
                        ⚡ Switch to {providers.find((p) => p.is_configured)?.name} (Ready)
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-[11px] text-[#727780] leading-relaxed">
                {activeProvider?.data_transmission_notice}
              </p>
            )}
          </div>

          {/* Privacy Disclosure and Explicit Consent Checkbox */}
          <div className="p-3.5 rounded bg-[#1D2018] border border-[#3E4929] flex flex-col gap-2.5">
            <div className="flex items-center gap-2 text-[12px] font-medium text-[#D8E7A2]">
              <ShieldCheck className="w-4 h-4 text-[#D8E7A2]" />
              <span>Privacy &amp; Data Minimization Disclosure</span>
            </div>
            <p className="text-[11px] text-[#A0A5AD] leading-relaxed">
              Generating this draft will transmit <strong>only minimal context</strong> (business name, category, city, website condition, and specific audit finding titles) to <strong>{activeProvider?.name}</strong>. No raw HTML crawl pages, customer databases, or secret credentials are ever transmitted.
            </p>

            <label className="flex items-center gap-2.5 cursor-pointer pt-1 border-t border-[#364024]">
              <input
                type="checkbox"
                checked={privacyConsent}
                onChange={(e) => setPrivacyConsent(e.target.checked)}
                disabled={isGenerating || !isProviderConfigured}
                className="w-4 h-4 rounded bg-[#141618] border-[#3E4929] text-[#D8E7A2] focus:ring-0 cursor-pointer"
              />
              <span className="text-[12px] text-[#F3F4F6] font-medium select-none">
                I explicitly consent to transmitting minimal prospect &amp; audit details to {activeProvider?.name || 'the AI provider'}.
              </span>
            </label>
          </div>

          {/* Generation Error Banner */}
          {generationError && (
            <div className="p-3 rounded bg-[#2A1818] border border-[#4A2626] text-[12px] text-[#D78383] flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium">Generation Request Failed</div>
                <div className="text-[11px] mt-0.5">{generationError}</div>
              </div>
            </div>
          )}

          {/* Progress Indicator */}
          {isGenerating && (
            <div className="p-3 rounded bg-[#1D2024] border border-[#3E4550] flex items-center gap-3 text-[12px] text-[#F3F4F6]">
              <RefreshCw className="w-4 h-4 text-[#D8E7A2] animate-spin shrink-0" />
              <div className="flex flex-col gap-0.5">
                <span className="font-medium">Synthesizing evidence-backed outreach letter...</span>
                <span className="text-[11px] text-[#727780]">Contacting {activeProvider?.name} · Cross-checking claims against audit report</span>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-[#24272D] flex items-center justify-between bg-[#1A1C20]">
          <div className="text-[11px] text-[#727780]">
            Zero email dispatch: Phase 5 creates drafts only.
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="ghost"
              size="md"
              onClick={onClose}
              disabled={isGenerating}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              isLoading={isGenerating}
              disabled={!isProviderConfigured || !privacyConsent || isGenerating}
              onClick={handleGenerate}
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Generate Email Draft
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
