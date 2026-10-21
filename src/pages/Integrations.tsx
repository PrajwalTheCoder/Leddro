import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import {
  Mail,
  Cpu,
  Compass,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  User,
  ShieldCheck,
  ExternalLink,
  Save,
  AlertTriangle,
  Key,
  Check,
  Eye,
  EyeOff,
  Sparkles,
  Search,
  Globe,
  Phone,
  Building2,
  Share2,
  MessageSquare
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { AIProviderStatus, AISettings } from '../types';

export const Integrations: React.FC = () => {
  const {
    integrations,
    googleStatus,
    fetchGoogleStatus,
    emailDispatchStatus,
    fetchEmailDispatchStatus,
    connectGoogle,
    testGoogleConnection,
    disconnectGoogle,
    addToast
  } = useApp();

  // AI Providers & Settings
  const [providers, setProviders] = useState<AIProviderStatus[]>([]);
  const [aiSettings, setAiSettings] = useState<AISettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // API Key insertion state per provider
  const [apiKeys, setApiKeys] = useState<{ [providerId: string]: string }>({});
  const [showKey, setShowKey] = useState<{ [providerId: string]: boolean }>({});
  const [isSavingKey, setIsSavingKey] = useState<{ [providerId: string]: boolean }>({});
  const [selectedModel, setSelectedModel] = useState<{ [providerId: string]: string }>({});
  const [customEndpoint, setCustomEndpoint] = useState<string>('');

  // Active testing state
  const [testingProviderId, setTestingProviderId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ provider_id: string; success: boolean; message: string; latency_ms?: number } | null>(null);

  // Phase 6 & Phase 8: Google OAuth and SMTP states
  const [isConnectingGoogle, setIsConnectingGoogle] = useState(false);
  const [isTestingGoogle, setIsTestingGoogle] = useState(false);
  const [isDisconnectingGoogle, setIsDisconnectingGoogle] = useState(false);
  const [googleTestDetails, setGoogleTestDetails] = useState<{ success: boolean; message: string; latency_ms?: number } | null>(null);
  const [googleOAuthError, setGoogleOAuthError] = useState<string | null>(null);
  const [isTestingSMTP, setIsTestingSMTP] = useState(false);
  const [smtpTestResult, setSmtpTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [smtpTestEmail, setSmtpTestEmail] = useState('');
  const [smtpTestPassword, setSmtpTestPassword] = useState('');
  const [showSmtpPassword, setShowSmtpPassword] = useState(false);
  const [showSmtpTester, setShowSmtpTester] = useState(false);

  const handleTestSMTP = async () => {
    setIsTestingSMTP(true);
    setSmtpTestResult(null);
    try {
      const payload: { user?: string; password?: string } = {};
      if (smtpTestEmail.trim() && smtpTestPassword.trim()) {
        payload.user = smtpTestEmail.trim();
        payload.password = smtpTestPassword.trim();
      }
      const res = await fetch('/api/email/test-smtp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setSmtpTestResult({ success: true, message: data.message || 'SMTP authentication verified successfully.' });
        addToast('SMTP authentication verified successfully', 'success');
        await fetchEmailDispatchStatus();
      } else {
        const errMsg = data.detail || 'SMTP test connection failed';
        setSmtpTestResult({ success: false, message: errMsg });
        addToast(errMsg, 'error');
      }
    } catch (err: any) {
      const errMsg = err.message || 'Failed to connect to SMTP server';
      setSmtpTestResult({ success: false, message: errMsg });
      addToast(errMsg, 'error');
    } finally {
      setIsTestingSMTP(false);
    }
  };

  // Contact Enrichment Providers (Hunter.io & Google Places)
  const [enrichmentStatus, setEnrichmentStatus] = useState<any>(null);
  const [hunterKey, setHunterKey] = useState('');
  const [showHunterKey, setShowHunterKey] = useState(false);
  const [isSavingHunter, setIsSavingHunter] = useState(false);
  const [isTestingHunter, setIsTestingHunter] = useState(false);
  const [hunterTestResult, setHunterTestResult] = useState<{ success: boolean; message: string; available_searches?: number; plan?: string } | null>(null);

  const [placesKey, setPlacesKey] = useState('');
  const [showPlacesKey, setShowPlacesKey] = useState(false);
  const [isSavingPlaces, setIsSavingPlaces] = useState(false);
  const [isTestingPlaces, setIsTestingPlaces] = useState(false);
  const [placesTestResult, setPlacesTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const fetchEnrichmentStatus = async () => {
    try {
      const res = await fetch('/api/enrichment/status');
      if (res.ok) {
        const data = await res.json();
        setEnrichmentStatus(data);
      }
    } catch {
      // silent
    }
  };

  useEffect(() => {
    fetchEnrichmentStatus();
  }, []);

  const handleSaveHunterKey = async () => {
    if (!hunterKey.trim()) return;
    setIsSavingHunter(true);
    try {
      const res = await fetch('/api/enrichment/save-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hunter_api_key: hunterKey.trim() })
      });
      const data = await res.json();
      if (res.ok) {
        addToast('Hunter.io API key saved securely to local .env', 'success');
        setHunterKey('');
        setEnrichmentStatus(data.status);
      } else {
        addToast(data.detail || 'Failed to save Hunter key', 'error');
      }
    } catch (err: any) {
      addToast(err.message, 'error');
    } finally {
      setIsSavingHunter(false);
    }
  };

  const handleTestHunter = async () => {
    setIsTestingHunter(true);
    setHunterTestResult(null);
    try {
      const payload: { api_key?: string } = {};
      if (hunterKey.trim()) payload.api_key = hunterKey.trim();
      const res = await fetch('/api/enrichment/test-hunter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setHunterTestResult(data);
      if (data.success) {
        addToast(`Hunter.io authenticated: ${data.available_searches || 25} searches remaining`, 'success');
        await fetchEnrichmentStatus();
      } else {
        addToast(data.message || 'Hunter.io connection failed', 'error');
      }
    } catch (err: any) {
      setHunterTestResult({ success: false, message: err.message });
      addToast(err.message, 'error');
    } finally {
      setIsTestingHunter(false);
    }
  };

  const handleSavePlacesKey = async () => {
    if (!placesKey.trim()) return;
    setIsSavingPlaces(true);
    try {
      const res = await fetch('/api/enrichment/save-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ google_places_api_key: placesKey.trim() })
      });
      const data = await res.json();
      if (res.ok) {
        addToast('Google Places API key saved securely to local .env', 'success');
        setPlacesKey('');
        setEnrichmentStatus(data.status);
      } else {
        addToast(data.detail || 'Failed to save Places key', 'error');
      }
    } catch (err: any) {
      addToast(err.message, 'error');
    } finally {
      setIsSavingPlaces(false);
    }
  };

  const handleTestPlaces = async () => {
    setIsTestingPlaces(true);
    setPlacesTestResult(null);
    try {
      const payload: { api_key?: string } = {};
      if (placesKey.trim()) payload.api_key = placesKey.trim();
      const res = await fetch('/api/enrichment/test-google-places', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setPlacesTestResult(data);
      if (data.success) {
        addToast(data.message, 'success');
        await fetchEnrichmentStatus();
      } else {
        addToast(data.message || 'Google Places connection failed', 'error');
      }
    } catch (err: any) {
      setPlacesTestResult({ success: false, message: err.message });
      addToast(err.message, 'error');
    } finally {
      setIsTestingPlaces(false);
    }
  };

  // Developer Profile form
  const [devName, setDevName] = useState('');
  const [devTitle, setDevTitle] = useState('');
  const [devServices, setDevServices] = useState('');
  const [devPortfolioUrl, setDevPortfolioUrl] = useState('');
  const [devEmail, setDevEmail] = useState('');
  const [devSignature, setDevSignature] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // Check URL for OAuth callback redirect parameters
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('google_connected') === 'true') {
      const email = params.get('email');
      addToast(email ? `Connected to Google account: ${email}` : 'Google OAuth connected successfully', 'success');
      fetchGoogleStatus();
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (params.get('google_error')) {
      const err = params.get('google_error') || 'Google authorization failed';
      setGoogleOAuthError(err);
      addToast(`Google OAuth error: ${err}`, 'error');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);


  const fetchAIState = async () => {
    setIsLoading(true);
    try {
      const [provRes, setRes] = await Promise.all([
        fetch('/api/ai/providers'),
        fetch('/api/ai/settings')
      ]);

      if (provRes.ok) {
        const provData = await provRes.json();
        setProviders(provData);
      }

      if (setRes.ok) {
        const setData: AISettings = await setRes.json();
        setAiSettings(setData);
        setDevName(setData.dev_name || '');
        setDevTitle(setData.dev_title || '');
        setDevServices(setData.dev_services || '');
        setDevPortfolioUrl(setData.dev_portfolio_url || '');
        setDevEmail(setData.dev_email || '');
        setDevSignature(setData.dev_signature || '');
      }
    } catch (e) {
      // Backend might be offline
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAIState();
  }, []);

  const handleSetActiveProvider = async (providerId: string) => {
    try {
      const res = await fetch('/api/ai/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active_provider: providerId })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to update active provider');
      }

      await fetchAIState();
      addToast(`Active AI engine set to ${providerId}`, 'success');
    } catch (err: any) {
      addToast(`Error updating provider: ${err.message}`, 'error');
    }
  };

  const handleSaveApiKey = async (providerId: string) => {
    const keyToSave = apiKeys[providerId]?.trim();
    if (!keyToSave && providerId !== 'compatible') {
      addToast('Please enter an API key to save', 'error');
      return;
    }

    setIsSavingKey(prev => ({ ...prev, [providerId]: true }));
    try {
      const body: any = {};
      if (providerId === 'gemini') {
        if (keyToSave) body.gemini_api_key = keyToSave;
        if (selectedModel['gemini']) body.gemini_model = selectedModel['gemini'];
      } else if (providerId === 'openai') {
        if (keyToSave) body.openai_api_key = keyToSave;
        if (selectedModel['openai']) body.openai_model = selectedModel['openai'];
      } else if (providerId === 'anthropic') {
        if (keyToSave) body.anthropic_api_key = keyToSave;
        if (selectedModel['anthropic']) body.anthropic_model = selectedModel['anthropic'];
      } else if (providerId === 'compatible') {
        if (keyToSave) body.compatible_api_key = keyToSave;
        if (customEndpoint.trim()) body.compatible_base_url = customEndpoint.trim();
        if (selectedModel['compatible']) body.compatible_model = selectedModel['compatible'];
      }

      const res = await fetch('/api/ai/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to save API key');
      }

      await fetchAIState();
      setApiKeys(prev => ({ ...prev, [providerId]: '' }));
      addToast(`API key & configuration saved successfully for ${providerId}`, 'success');
    } catch (err: any) {
      addToast(`Failed to save key: ${err.message}`, 'error');
    } finally {
      setIsSavingKey(prev => ({ ...prev, [providerId]: false }));
    }
  };

  const handleTestConnection = async (providerId: string) => {
    setTestingProviderId(providerId);
    setTestResult(null);

    try {
      const res = await fetch('/api/ai/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: providerId })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `Connection failed (HTTP ${res.status})`);
      }

      setTestResult({
        provider_id: providerId,
        success: true,
        message: data.message || 'Connection verified successfully.',
        latency_ms: data.latency_ms
      });
      addToast(`Connected to ${providerId} (${data.latency_ms}ms latency)`, 'success');
    } catch (err: any) {
      setTestResult({
        provider_id: providerId,
        success: false,
        message: err.message
      });
      addToast(`Connection failed: ${err.message}`, 'error');
    } finally {
      setTestingProviderId(null);
    }
  };

  const handleSaveDeveloperProfile = async () => {
    setIsSavingProfile(true);
    try {
      const res = await fetch('/api/ai/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dev_name: devName,
          dev_title: devTitle,
          dev_services: devServices,
          dev_portfolio_url: devPortfolioUrl,
          dev_email: devEmail,
          dev_signature: devSignature
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to save profile settings');
      }

      const updated = await res.json();
      setAiSettings(updated);
      addToast('Developer profile context updated successfully', 'success');
    } catch (err: any) {
      addToast(`Failed to save profile: ${err.message}`, 'error');
    } finally {
      setIsSavingProfile(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#111214]">
      {/* Header */}
      <div className="px-6 pt-5 pb-3 border-b border-[#22252A] flex flex-col gap-1 shrink-0">
        <div className="flex items-center gap-2">
          <h1 className="text-[24px] font-semibold text-[#F3F4F6] tracking-tight">
            Integrations &amp; Providers
          </h1>
          <span className="font-mono text-[11px] text-[#D8E7A2] bg-[#22271B] px-2 py-0.5 rounded border border-[#364024]">
            Phase 5 Configured
          </span>
        </div>
        <p className="text-[12px] text-[#A0A5AD]">
          Configure deterministic scrapers, AI reasoning providers, and developer outreach identity.
        </p>
      </div>

      {/* Main Container */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 max-w-5xl">
        {/* Section 1: AI Reasoning & Draft Synthesis Providers */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#D8E7A2]" />
              <h2 className="text-[15px] font-semibold text-[#F3F4F6]">
                AI Provider Architecture
              </h2>
            </div>
            <span className="text-[11px] text-[#727780] font-mono">
              Active: {aiSettings?.active_provider || 'openai'} ({aiSettings?.active_model || 'gpt-4o-mini'})
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {providers.map((p) => {
              const isActive = (aiSettings?.active_provider || 'openai') === p.provider_id;
              const isTesting = testingProviderId === p.provider_id;
              const resultForThis = testResult && testResult.provider_id === p.provider_id ? testResult : null;

              return (
                <div
                  key={p.provider_id}
                  className={`rounded border p-4.5 flex flex-col gap-3 transition-colors ${
                    isActive
                      ? 'bg-[#17191C] border-[#3E4929]'
                      : 'bg-[#141618] border-[#2B2F36]'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#24272D] pb-3">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleSetActiveProvider(p.provider_id)}
                        className={`w-5 h-5 rounded-full border flex items-center justify-center transition-colors ${
                          isActive
                            ? 'border-[#D8E7A2] bg-[#22271B] text-[#D8E7A2]'
                            : 'border-[#4A505C] hover:border-[#A0A5AD]'
                        }`}
                        title={isActive ? 'Active engine' : 'Set as active engine'}
                      >
                        {isActive && <div className="w-2.5 h-2.5 rounded-full bg-[#D8E7A2]" />}
                      </button>

                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-[14px] font-medium text-[#F3F4F6]">{p.name}</h3>
                          {(p.provider_id === 'gemini' || p.is_free_tier) && (
                            <span className="font-mono text-[10px] text-[#A2E7B5] bg-[#18261F] px-1.5 py-0.5 rounded border border-[#253D30] font-semibold flex items-center gap-1">
                              <Sparkles className="w-2.5 h-2.5 text-[#D8E7A2]" />
                              100% Free Tier (Google AI Studio)
                            </span>
                          )}
                          {p.is_local && (
                            <span className="font-mono text-[10px] text-[#91B7D8] bg-[#182330] px-1.5 py-0.5 rounded border border-[#273B52]">
                              Local-Only / Self-Hosted
                            </span>
                          )}
                          <span className={`font-mono text-[11px] px-2 py-0.5 rounded border ${
                            p.is_configured
                              ? 'bg-[#18261F] text-[#80B89A] border-[#253D30]'
                              : 'bg-[#2A1818] text-[#D78383] border-[#4A2626]'
                          }`}>
                            {p.is_configured ? 'Configured' : 'Missing Key / Endpoint'}
                          </span>
                        </div>
                        <p className="text-[12px] text-[#727780] mt-0.5">{p.status_message}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {!isActive && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSetActiveProvider(p.provider_id)}
                        >
                          Select Active
                        </Button>
                      )}
                      <Button
                        variant="secondary"
                        size="sm"
                        isLoading={isTesting}
                        onClick={() => handleTestConnection(p.provider_id)}
                        leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                      >
                        Test Connection
                      </Button>
                    </div>
                  </div>

                  {/* Provider Parameters & Masked Keys */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[12px]">
                    <div className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1">
                      <span className="text-[10px] text-[#727780] uppercase tracking-wider font-medium">Model ID</span>
                      <span className="font-mono text-[#F3F4F6]">{p.current_model}</span>
                    </div>

                    <div className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1">
                      <span className="text-[10px] text-[#727780] uppercase tracking-wider font-medium">Credential Security</span>
                      <span className="font-mono text-[#A0A5AD]">
                        {p.provider_id === 'gemini' ? (aiSettings?.gemini_masked_key || 'Not configured') :
                         p.provider_id === 'openai' ? (aiSettings?.openai_masked_key || 'Not configured') :
                         p.provider_id === 'anthropic' ? (aiSettings?.anthropic_masked_key || 'Not configured') :
                         'No key required (Local Ollama)'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1">
                      <span className="text-[10px] text-[#727780] uppercase tracking-wider font-medium">Privacy Scope</span>
                      <span className="text-[11px] text-[#727780] leading-tight">
                        {p.is_local ? '100% on-device inference' : 'Minimal context transmission'}
                      </span>
                    </div>
                  </div>

                  {/* Inline Insert / Update API Key Form */}
                  <div className="pt-2 border-t border-[#22252A] flex flex-col gap-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-[#A0A5AD] font-medium flex items-center gap-1.5">
                        <Key className="w-3.5 h-3.5 text-[#D8E7A2]" />
                        {p.is_configured ? 'Insert / Update API Key' : 'Insert Your API Key'}
                      </span>
                      {p.provider_id === 'gemini' && (
                        <a
                          href="https://aistudio.google.com/app/apikey"
                          target="_blank"
                          rel="noreferrer"
                          className="text-[#D8E7A2] hover:underline flex items-center gap-1 font-mono text-[11px]"
                        >
                          <span>Get Free Key at Google AI Studio</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                      {p.provider_id === 'openai' && (
                        <a
                          href="https://platform.openai.com/api-keys"
                          target="_blank"
                          rel="noreferrer"
                          className="text-[#91B7D8] hover:underline flex items-center gap-1 font-mono text-[11px]"
                        >
                          <span>OpenAI Platform API Keys</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                      {p.provider_id === 'anthropic' && (
                        <a
                          href="https://console.anthropic.com/"
                          target="_blank"
                          rel="noreferrer"
                          className="text-[#D78383] hover:underline flex items-center gap-1 font-mono text-[11px]"
                        >
                          <span>Anthropic Console Keys</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>

                    <div className="flex flex-col sm:flex-row gap-2">
                      <div className="relative flex-1">
                        <input
                          type={showKey[p.provider_id] ? "text" : "password"}
                          value={apiKeys[p.provider_id] || ''}
                          onChange={(e) => setApiKeys({ ...apiKeys, [p.provider_id]: e.target.value })}
                          placeholder={
                            p.provider_id === 'gemini' ? (aiSettings?.gemini_configured && aiSettings.gemini_masked_key ? `Configured (${aiSettings.gemini_masked_key}) — paste new to update` : "Insert Gemini API Key (e.g. AIzaSy...)") :
                            p.provider_id === 'openai' ? (aiSettings?.openai_configured && aiSettings.openai_masked_key ? `Configured (${aiSettings.openai_masked_key}) — paste new to update` : "Insert OpenAI API Key (e.g. sk-proj-...)") :
                            p.provider_id === 'anthropic' ? (aiSettings?.anthropic_configured && aiSettings.anthropic_masked_key ? `Configured (${aiSettings.anthropic_masked_key}) — paste new to update` : "Insert Anthropic API Key (e.g. sk-ant-...)") :
                            "Optional API key for remote vLLM/proxy"
                          }
                          className="w-full bg-[#111214] border border-[#2B2F36] rounded px-3 py-1.5 text-[12px] font-mono text-[#F3F4F6] placeholder-[#555B66] focus:outline-none focus:border-[#D8E7A2] pr-8"
                        />
                        <button
                          type="button"
                          onClick={() => setShowKey({ ...showKey, [p.provider_id]: !showKey[p.provider_id] })}
                          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#727780] hover:text-[#A0A5AD]"
                          title={showKey[p.provider_id] ? "Hide key" : "Show key"}
                        >
                          {showKey[p.provider_id] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>

                      {p.provider_id === 'compatible' && (
                        <input
                          type="text"
                          value={customEndpoint || aiSettings?.compatible_base_url || 'http://localhost:11434/v1'}
                          onChange={(e) => setCustomEndpoint(e.target.value)}
                          placeholder="Endpoint (http://localhost:11434/v1)"
                          className="w-full sm:w-60 bg-[#111214] border border-[#2B2F36] rounded px-3 py-1.5 text-[12px] font-mono text-[#F3F4F6] focus:outline-none focus:border-[#D8E7A2]"
                        />
                      )}

                      {p.available_models && p.available_models.length > 0 && (
                        <select
                          value={selectedModel[p.provider_id] || p.current_model}
                          onChange={(e) => setSelectedModel({ ...selectedModel, [p.provider_id]: e.target.value })}
                          className="bg-[#111214] border border-[#2B2F36] rounded px-2.5 py-1.5 text-[12px] font-mono text-[#F3F4F6] focus:outline-none focus:border-[#D8E7A2]"
                        >
                          {Array.from(new Set(p.available_models || [])).map((m) => (
                            <option key={m} value={m} className="bg-[#181A1D]">
                              {m}
                            </option>
                          ))}
                        </select>
                      )}

                      <Button
                        variant="secondary"
                        size="sm"
                        isLoading={isSavingKey[p.provider_id]}
                        onClick={() => handleSaveApiKey(p.provider_id)}
                        leftIcon={<Save className="w-3.5 h-3.5" />}
                        className="shrink-0"
                      >
                        Save Key
                      </Button>
                    </div>
                  </div>

                  {/* Test Connection Result Banner */}
                  {resultForThis && (
                    <div className={`p-2.5 rounded border text-[11px] flex items-center justify-between font-mono ${
                      resultForThis.success
                        ? 'bg-[#18261F] border-[#253D30] text-[#80B89A]'
                        : 'bg-[#2A1818] border-[#4A2626] text-[#D78383]'
                    }`}>
                      <div className="flex items-center gap-2">
                        {resultForThis.success ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                        <span>{resultForThis.message}</span>
                      </div>
                      {resultForThis.latency_ms && (
                        <span>{resultForThis.latency_ms} ms</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Privacy & Key Storage Notice */}
          <div className="p-3.5 rounded bg-[#17191C] border border-[#2B2F36] flex flex-col gap-2 text-[12px] text-[#A0A5AD]">
            <div className="flex items-center gap-2 text-[#D8E7A2] font-medium">
              <ShieldCheck className="w-4 h-4 text-[#D8E7A2]" />
              <span>API Key &amp; Privacy Management</span>
            </div>
            <p className="text-[11px] text-[#727780] leading-relaxed">
              Leddro is local-first. You can insert API keys directly above (persisted locally to your secure <code className="text-[#F3F4F6]">.env</code> file) or load them automatically from your system environment. Keys are never exposed to browser storage, and never logged.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px] font-mono pt-1 border-t border-[#24272D]">
              <div className="p-2 rounded bg-[#111214] border border-[#24272D]">
                <div className="flex items-center gap-1 text-[#A2E7B5] font-semibold">
                  <Sparkles className="w-3 h-3 text-[#D8E7A2]" />
                  <span>Google Gemini (Free):</span>
                </div>
                <div className="text-[#727780] mt-0.5">Google AI Studio free tier key:</div>
                <div className="text-[#D8E7A2] truncate">GEMINI_API_KEY="AIza..."</div>
              </div>
              <div className="p-2 rounded bg-[#111214] border border-[#24272D]">
                <strong className="text-[#F3F4F6]">Windows Setup:</strong>
                <div className="text-[#727780] mt-0.5">Edit <code className="text-[#A0A5AD]">.env</code> or insert key above:</div>
                <div className="text-[#D8E7A2] truncate">OPENAI_API_KEY="sk-..."</div>
              </div>
              <div className="p-2 rounded bg-[#111214] border border-[#24272D]">
                <strong className="text-[#F3F4F6]">Local Ollama Setup:</strong>
                <div className="text-[#727780] mt-0.5">Run Ollama on your machine:</div>
                <div className="text-[#D8E7A2]">ollama run llama3</div>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Developer Profile Context */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-[#D8E7A2]" />
              <h2 className="text-[15px] font-semibold text-[#F3F4F6]">
                Developer Profile &amp; Outreach Identity
              </h2>
            </div>
            <span className="text-[11px] text-[#727780]">Anchors email signature and offered capabilities</span>
          </div>

          <div className="rounded border border-[#2B2F36] bg-[#17191C] p-5 flex flex-col gap-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Full Name / Sender Name
                </label>
                <input
                  type="text"
                  value={devName}
                  onChange={(e) => setDevName(e.target.value)}
                  placeholder="e.g. Lisa Nguyen"
                  className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Professional Title
                </label>
                <input
                  type="text"
                  value={devTitle}
                  onChange={(e) => setDevTitle(e.target.value)}
                  placeholder="e.g. Independent Web Consultant & Full-Stack Developer"
                  className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Core Services Offered
                </label>
                <input
                  type="text"
                  value={devServices}
                  onChange={(e) => setDevServices(e.target.value)}
                  placeholder="e.g. Website performance tuning, modern responsive redesigns, SSL/DNS remediation"
                  className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[12px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Contact Email
                </label>
                <input
                  type="email"
                  value={devEmail}
                  onChange={(e) => setDevEmail(e.target.value)}
                  placeholder="contact@leddro.local"
                  className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[12px] font-mono text-[#F3F4F6] focus:border-[#4B5361] outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Portfolio / Agency Website URL <span className="text-[#727780] lowercase">(optional)</span>
                </label>
                <input
                  type="url"
                  value={devPortfolioUrl}
                  onChange={(e) => setDevPortfolioUrl(e.target.value)}
                  placeholder="https://example.dev"
                  className="w-full bg-[#111214] border border-[#30343A] rounded px-3 py-1.5 text-[12px] font-mono text-[#F3F4F6] focus:border-[#4B5361] outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-[11px] font-medium text-[#A0A5AD] uppercase tracking-wider mb-1">
                  Default Email Signature
                </label>
                <textarea
                  value={devSignature}
                  onChange={(e) => setDevSignature(e.target.value)}
                  rows={3}
                  placeholder="Best regards,&#10;Lisa Nguyen&#10;Lead Consultant"
                  className="w-full bg-[#111214] border border-[#30343A] rounded p-2.5 text-[12px] font-sans text-[#F3F4F6] focus:border-[#4B5361] outline-none resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#24272D]">
              <Button
                variant="primary"
                size="md"
                isLoading={isSavingProfile}
                onClick={handleSaveDeveloperProfile}
                leftIcon={<Save className="w-4 h-4" />}
              >
                Save Developer Profile
              </Button>
            </div>
          </div>
        </div>

        {/* Section 3: Direct SMTP Gateway (Google App Password) - PREFERRED */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2.5">
              <Mail className="w-4 h-4 text-[#D8E7A2]" />
              <h2 className="text-[15px] font-semibold text-[#F3F4F6]">
                Direct SMTP Gateway (Google App Password)
              </h2>
              <span className="inline-flex items-center gap-1 font-mono text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border bg-[#202718] text-[#D8E7A2] border-[#3B4D22] shadow-[0_0_12px_rgba(216,231,162,0.12)]">
                <Sparkles className="w-3 h-3 text-[#D8E7A2]" /> Preferred · Fastest (30s)
              </span>
            </div>
            {emailDispatchStatus?.method === 'smtp' ? (
              <span className="inline-flex items-center gap-1.5 font-mono text-[11px] px-2.5 py-0.5 rounded border bg-[#18261F] text-[#80B89A] border-[#253D30]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#80B89A]" />
                Active Dispatch Method
              </span>
            ) : emailDispatchStatus?.smtp_configured ? (
              <span className="inline-flex items-center gap-1.5 font-mono text-[11px] px-2.5 py-0.5 rounded border bg-[#1D2530] text-[#91B7D8] border-[#2B3A4F]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#91B7D8]" />
                Configured (Ready)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 font-mono text-[11px] px-2.5 py-0.5 rounded border bg-[#212328] text-[#727780] border-[#30343A]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#727780]" />
                Not Configured
              </span>
            )}
          </div>

          <div className="rounded border border-[#2B2F36] bg-[#17191C] p-5 flex flex-col gap-4">
            {/* Account Card Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#24272D] pb-4">
              <div className="flex items-start sm:items-center gap-3">
                <div className={`w-11 h-11 rounded-lg border flex items-center justify-center shrink-0 ${
                  emailDispatchStatus?.smtp_configured
                    ? 'bg-[#18261F] border-[#253D30] text-[#80B89A]'
                    : 'bg-[#1D2024] border-[#30343A] text-[#727780]'
                }`}>
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-[14px] font-medium text-[#F3F4F6]">
                      {emailDispatchStatus?.sender_email ? (
                        <span className="font-mono">{emailDispatchStatus.sender_email}</span>
                      ) : (
                        'Gmail SMTP Gateway'
                      )}
                    </h3>
                    {emailDispatchStatus?.smtp_configured && (
                      <span className="font-mono text-[10px] bg-[#18261F] text-[#80B89A] border border-[#253D30] px-1.5 py-0.2 rounded flex items-center gap-1">
                        <Check className="w-3 h-3" /> Configured in .env
                      </span>
                    )}
                  </div>
                  <p className="text-[12px] text-[#727780] mt-0.5">
                    Direct TLS delivery using a 16-character Google App Password. Zero Google Cloud Console setup or OAuth client needed.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={(!emailDispatchStatus?.smtp_configured && (!smtpTestEmail.trim() || !smtpTestPassword.trim())) || isTestingSMTP}
                  isLoading={isTestingSMTP}
                  onClick={handleTestSMTP}
                  leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                >
                  Test SMTP Connection
                </Button>
                <Button
                  variant="accent-subtle"
                  size="sm"
                  onClick={() => setShowSmtpTester(!showSmtpTester)}
                  leftIcon={<Key className="w-3.5 h-3.5 text-[#D8E7A2]" />}
                >
                  {showSmtpTester ? 'Hide Quick Test' : 'Test Credentials'}
                </Button>
              </div>
            </div>

            {/* Test Connection Result Box */}
            {smtpTestResult && (
              <div className={`p-3 rounded text-[12px] border ${
                smtpTestResult.success
                  ? 'bg-[#16211B] border-[#2D4536] text-[#80B89A]'
                  : 'bg-[#241515] border-[#4D2424] text-[#D78383]'
              }`}>
                <div className="flex items-center gap-2">
                  {smtpTestResult.success ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
                  <span>{smtpTestResult.message}</span>
                </div>
              </div>
            )}

            {/* Quick Test Inline Form (Optional) */}
            {showSmtpTester && (
              <div className="p-4 rounded bg-[#131518] border border-[#2E333B] flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[12px] font-medium text-[#F3F4F6]">
                    <Key className="w-3.5 h-3.5 text-[#D8E7A2]" />
                    <span>Quick Test Google App Password (Live TLS Verification)</span>
                  </div>
                  <span className="text-[11px] text-[#727780]">Tested safely over TLS without logging</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-mono text-[#727780] mb-1">Gmail Address (SMTP_USER)</label>
                    <input
                      type="email"
                      value={smtpTestEmail}
                      onChange={(e) => setSmtpTestEmail(e.target.value)}
                      placeholder="your.email@gmail.com"
                      className="w-full bg-[#1A1D21] border border-[#2B2F36] rounded px-3 py-1.5 text-[12px] font-mono text-[#F3F4F6] placeholder-[#555A64] focus:border-[#4B5361] outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-mono text-[#727780] mb-1">16-Character App Password (SMTP_PASSWORD)</label>
                    <div className="relative">
                      <input
                        type={showSmtpPassword ? 'text' : 'password'}
                        value={smtpTestPassword}
                        onChange={(e) => setSmtpTestPassword(e.target.value)}
                        placeholder="xxxx xxxx xxxx xxxx"
                        className="w-full bg-[#1A1D21] border border-[#2B2F36] rounded pl-3 pr-9 py-1.5 text-[12px] font-mono text-[#F3F4F6] placeholder-[#555A64] focus:border-[#4B5361] outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setShowSmtpPassword(!showSmtpPassword)}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#727780] hover:text-[#F3F4F6]"
                      >
                        {showSmtpPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[11px] text-[#A0A5AD]">
                    Enter credentials above and click <strong>Test SMTP Connection</strong> to test live. Once verified, copy them to your <code className="font-mono text-[#F3F4F6]">.env</code>.
                  </span>
                </div>
              </div>
            )}

            {/* Step-by-Step Setup Guide */}
            <div className="p-4 rounded bg-[#182015] border border-[#2F4420] text-[12px] flex flex-col gap-2.5 text-[#C9DC95]">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2 font-medium text-[#F3F4F6]">
                  <Sparkles className="w-4 h-4 text-[#D8E7A2]" />
                  <span>How to Complete SMTP Setup in 30 Seconds</span>
                </div>
                <span className="font-mono text-[10px] uppercase bg-[#202C1B] text-[#D8E7A2] border border-[#3E5A2A] px-2 py-0.5 rounded">
                  Preferred / Recommended Method
                </span>
              </div>
              <p className="text-[12px] leading-relaxed text-[#A0A5AD]">
                Follow these 5 simple steps to connect your Gmail account instantly. No Google Cloud Console, app verification, or OAuth client setup required:
              </p>
              <div className="mt-1 pt-2 border-t border-[#2F4420] text-[11px] text-[#A0A5AD] leading-relaxed">
                <ol className="list-decimal list-inside space-y-2 text-[#C5C9D0]">
                  <li>
                    <strong className="text-[#F3F4F6]">Turn ON 2-Step Verification:</strong> Go to{' '}
                    <a href="https://myaccount.google.com/security" target="_blank" rel="noreferrer" className="text-[#D8E7A2] hover:underline inline-flex items-center gap-0.5">
                      Google Account Security <ExternalLink className="w-3 h-3 inline ml-0.5" />
                    </a>{' '}
                    and ensure 2-Step Verification is active.
                  </li>
                  <li>
                    <strong className="text-[#F3F4F6]">Generate an App Password:</strong> Open{' '}
                    <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="text-[#D8E7A2] hover:underline inline-flex items-center gap-0.5">
                      myaccount.google.com/apppasswords <ExternalLink className="w-3 h-3 inline ml-0.5" />
                    </a>{' '}
                    (or search "App passwords" in Google Account settings).
                  </li>
                  <li>
                    <strong className="text-[#F3F4F6]">Name the App:</strong> Type <code className="font-mono text-[#D8E7A2] bg-[#111315] px-1.5 py-0.5 rounded border border-[#2B2F36]">Leddro</code> and click <strong className="text-[#F3F4F6]">Create</strong>. Google will generate a 16-character password (e.g., <code className="font-mono text-[#D8E7A2] bg-[#111315] px-1.5 py-0.5 rounded border border-[#2B2F36]">abcd efgh ijkl mnop</code>).
                  </li>
                  <li>
                    <strong className="text-[#F3F4F6]">Save in your <code className="font-mono text-[#F3F4F6]">.env</code> file:</strong> Open the <code className="font-mono text-[#F3F4F6]">.env</code> file in your Leddro root directory and add or update:
                    <div className="mt-2 p-3 rounded bg-[#111315] border border-[#2B2F36] font-mono text-[11px] text-[#D8E7A2] space-y-1 select-all">
                      <div>SMTP_HOST=smtp.gmail.com</div>
                      <div>SMTP_PORT=587</div>
                      <div>SMTP_USER=your.email@gmail.com</div>
                      <div>SMTP_PASSWORD=abcd efgh ijkl mnop</div>
                    </div>
                  </li>
                  <li>
                    <strong className="text-[#F3F4F6]">Test &amp; Send:</strong> Click <strong className="text-[#F3F4F6]">"Test SMTP Connection"</strong> above to confirm TLS delivery. Once verified, all approved client outreach emails will send directly from your personal Gmail!
                  </li>
                </ol>
              </div>
            </div>

            {/* SMTP Details Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[12px]">
              <div className="rounded bg-[#141618] border border-[#262A30] p-3 flex flex-col gap-1">
                <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">SMTP Gateway Host</span>
                <span className="font-mono text-[12px] text-[#F3F4F6] mt-0.5">
                  {emailDispatchStatus?.smtp_host || 'smtp.gmail.com'}:{emailDispatchStatus?.smtp_port || 587}
                </span>
                <span className="text-[10px] text-[#727780]">STARTTLS Encrypted (Port 587)</span>
              </div>

              <div className="rounded bg-[#141618] border border-[#262A30] p-3 flex flex-col gap-1">
                <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">Authentication</span>
                <span className="font-mono text-[12px] text-[#F3F4F6] mt-0.5">
                  Google App Password
                </span>
                <span className="text-[10px] text-[#727780]">Zero Cloud Console overhead</span>
              </div>

              <div className="rounded bg-[#141618] border border-[#262A30] p-3 flex flex-col gap-1">
                <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">Dispatch Routing</span>
                <span className="font-mono text-[12px] text-[#80B89A] mt-0.5">
                  {emailDispatchStatus?.method === 'smtp' ? 'Active Dispatcher' : 'Ready / Deterministic'}
                </span>
                <span className="text-[10px] text-[#727780]">Direct delivery without third-party APIs</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 3.1: Enterprise Google Cloud OAuth 2.0 & Gmail API Gateway */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-[#80B89A]" />
              <h2 className="text-[15px] font-semibold text-[#F3F4F6] flex items-center gap-2">
                <span>Google Gmail API Gateway (OAuth 2.0)</span>
                <span className="font-mono text-[10px] text-[#727780] bg-[#1E2024] px-2 py-0.5 rounded border border-[#2E3238]">
                  Alternative Method · Enterprise Cloud
                </span>
              </h2>
            </div>
            {googleStatus?.is_connected ? (
              <span className="inline-flex items-center gap-1.5 font-mono text-[11px] px-2.5 py-0.5 rounded border bg-[#18261F] text-[#80B89A] border-[#253D30]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#80B89A]" />
                Connected to Google
              </span>
            ) : googleStatus?.requires_reauth ? (
              <span className="inline-flex items-center gap-1.5 font-mono text-[11px] px-2.5 py-0.5 rounded border bg-[#2A2417] text-[#D8B16C] border-[#4A3D22]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#D8B16C]" />
                Reauthorization Required
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 font-mono text-[11px] px-2.5 py-0.5 rounded border bg-[#212328] text-[#727780] border-[#30343A]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#727780]" />
                Not Connected
              </span>
            )}
          </div>

          <div className="rounded border border-[#2B2F36] bg-[#17191C] p-5 flex flex-col gap-4">
            {/* OAuth Error Alert */}
            {googleOAuthError && (
              <div className="p-3.5 rounded bg-[#2A1818] border border-[#4A2626] text-[12px] text-[#D78383] flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-medium text-[#F3F4F6]">Google Authentication Error</div>
                  <div className="mt-0.5">{googleOAuthError}</div>
                </div>
                <button
                  onClick={() => setGoogleOAuthError(null)}
                  className="text-[#727780] hover:text-[#F3F4F6]"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Unconfigured Notice */}
            {googleStatus && !googleStatus.is_configured && (
              <div className="p-4 rounded bg-[#2A2417] border border-[#4A3D22] text-[12px] flex flex-col gap-2.5 text-[#D8B16C]">
                <div className="flex items-center gap-2 font-medium text-[#F3F4F6]">
                  <AlertTriangle className="w-4 h-4 text-[#D8B16C]" />
                  <span>Google Cloud OAuth Credentials Required</span>
                </div>
                <p className="text-[12px] leading-relaxed text-[#A0A5AD]">
                  To connect via OAuth 2.0, configure your Google Cloud OAuth application. Missing configuration keys:
                </p>
                <div className="flex flex-wrap gap-2">
                  {googleStatus.missing_config.map((key) => (
                    <span key={key} className="font-mono text-[11px] bg-[#1D2024] px-2 py-0.5 rounded border border-[#3E341F] text-[#F3F4F6]">
                      {key}
                    </span>
                  ))}
                </div>
                <div className="mt-1 pt-2 border-t border-[#3E341F] text-[11px] text-[#A0A5AD] leading-relaxed">
                  <strong>Quick Setup Steps:</strong>
                  <ol className="list-decimal list-inside mt-1 space-y-0.5">
                    <li>Create or select a project in <a href="https://console.cloud.google.com" target="_blank" rel="noreferrer" className="text-[#D8E7A2] hover:underline">Google Cloud Console</a>.</li>
                    <li>Enable the <strong>Gmail API</strong> in APIs &amp; Services.</li>
                    <li>Configure OAuth consent screen (Testing mode; add your email under Test Users).</li>
                    <li>Create an <strong>OAuth 2.0 Web Client</strong> with Authorized redirect URI: <code className="font-mono text-[#F3F4F6]">http://localhost:8000/api/google/callback</code>.</li>
                    <li>Add <code className="font-mono text-[#F3F4F6]">GOOGLE_CLIENT_ID</code> and <code className="font-mono text-[#F3F4F6]">GOOGLE_CLIENT_SECRET</code> to your backend environment or <code className="font-mono">.env</code> file.</li>
                  </ol>
                </div>
              </div>
            )}

            {/* Account Card Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#24272D] pb-4">
              <div className="flex items-start sm:items-center gap-3">
                <div className={`w-11 h-11 rounded-lg border flex items-center justify-center shrink-0 ${
                  googleStatus?.is_connected
                    ? 'bg-[#18261F] border-[#253D30] text-[#80B89A]'
                    : 'bg-[#1D2024] border-[#30343A] text-[#727780]'
                }`}>
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-[14px] font-medium text-[#F3F4F6]">
                      {googleStatus?.is_connected && googleStatus.email ? (
                        <span className="font-mono">{googleStatus.email}</span>
                      ) : (
                        'Google Account'
                      )}
                    </h3>
                    {googleStatus?.is_connected && (
                      <span className="font-mono text-[10px] bg-[#18261F] text-[#80B89A] border border-[#253D30] px-1.5 py-0.2 rounded flex items-center gap-1">
                        <Check className="w-3 h-3" /> Verified Identity
                      </span>
                    )}
                  </div>
                  <p className="text-[12px] text-[#727780] mt-0.5">
                    {googleStatus?.is_connected
                      ? 'Authenticated via official Google OAuth 2.0. Tokens encrypted locally with Fernet AES-128.'
                      : 'Connect your authenticated Google account to send individual approved outreach letters.'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {googleStatus?.is_connected ? (
                  <>
                    <Button
                      variant="secondary"
                      size="sm"
                      isLoading={isTestingGoogle}
                      onClick={async () => {
                        setIsTestingGoogle(true);
                        setGoogleTestDetails(null);
                        const res = await testGoogleConnection();
                        setGoogleTestDetails(res);
                        setIsTestingGoogle(false);
                      }}
                      leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                    >
                      Test Connection
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      isLoading={isDisconnectingGoogle}
                      onClick={async () => {
                        setIsDisconnectingGoogle(true);
                        await disconnectGoogle();
                        setIsDisconnectingGoogle(false);
                      }}
                    >
                      Disconnect
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="primary"
                    size="md"
                    disabled={isConnectingGoogle || (googleStatus !== null && !googleStatus.is_configured)}
                    isLoading={isConnectingGoogle}
                    onClick={async () => {
                      setIsConnectingGoogle(true);
                      await connectGoogle();
                      setIsConnectingGoogle(false);
                    }}
                    leftIcon={<Mail className="w-4 h-4" />}
                  >
                    Connect Google Account
                  </Button>
                )}
              </div>
            </div>

            {/* Test Connection Result Box */}
            {googleTestDetails && (
              <div className={`p-3 rounded text-[12px] border ${
                googleTestDetails.success
                  ? 'bg-[#16211B] border-[#2D4536] text-[#80B89A]'
                  : 'bg-[#241515] border-[#4D2424] text-[#D78383]'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {googleTestDetails.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>{googleTestDetails.message}</span>
                  </div>
                  {googleTestDetails.latency_ms && (
                    <span className="font-mono text-[11px] text-[#A0A5AD]">
                      API Latency: {googleTestDetails.latency_ms}ms
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Connected Details Grid */}
            {googleStatus?.is_connected ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[12px]">
                <div className="rounded bg-[#141618] border border-[#262A30] p-3 flex flex-col gap-1">
                  <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">Granted Scopes</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {googleStatus.scopes && googleStatus.scopes.length > 0 ? (
                      googleStatus.scopes.map((s) => (
                        <span key={s} className="font-mono text-[10px] bg-[#1D2024] text-[#A0A5AD] px-1.5 py-0.5 rounded border border-[#2B2F36]">
                          {s.split('/').pop()}
                        </span>
                      ))
                    ) : (
                      <span className="font-mono text-[11px] text-[#80B89A]">gmail.send</span>
                    )}
                  </div>
                </div>

                <div className="rounded bg-[#141618] border border-[#262A30] p-3 flex flex-col gap-1">
                  <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">Connection Established</span>
                  <span className="font-mono text-[12px] text-[#F3F4F6] mt-0.5">
                    {googleStatus.connected_at || 'Active Session'}
                  </span>
                  <span className="text-[11px] text-[#727780]">
                    Last Verified: {googleStatus.last_verified || 'Recent'}
                  </span>
                </div>

                <div className="rounded bg-[#141618] border border-[#262A30] p-3 flex flex-col gap-1">
                  <span className="text-[11px] text-[#727780] uppercase tracking-wider font-medium">Privacy Safeguards</span>
                  <div className="flex items-center gap-1.5 text-[11px] text-[#80B89A] mt-0.5">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Send-Only Scope (Zero Inbox Reading)</span>
                  </div>
                  <span className="text-[10px] text-[#727780]">
                    Encrypted SQLite credentials storage
                  </span>
                </div>
              </div>
            ) : (
              <div className="rounded bg-[#141618] border border-[#262A30] p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[12px] text-[#727780]">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-[#80B89A] shrink-0" />
                  <span>Leddro requests only <code className="font-mono text-[#A0A5AD]">gmail.send</code> permission. It never reads, indexes, or stores your personal inbox messages.</span>
                </div>
                <span className="font-mono text-[11px] text-[#A0A5AD] shrink-0">Official Google OAuth 2.0</span>
              </div>
            )}
          </div>
        </div>

        {/* Section 4: Contact Intelligence & B2B Email Discovery Gateways */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2.5">
              <Search className="w-4 h-4 text-[#D8E7A2]" />
              <h2 className="text-[15px] font-semibold text-[#F3F4F6]">
                Contact Intelligence &amp; B2B Email Discovery Gateways
              </h2>
              <span className="font-mono text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border bg-[#1B2217] text-[#D8E7A2] border-[#364923]">
                Zero Fake Emails
              </span>
            </div>
            <span className="text-[11px] text-[#727780]">
              Autonomous scrapers, DNS MX deliverability verification &amp; B2B directory lookups
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {/* Provider 1: Built-in Deterministic Website Contact Scraper */}
            <div className="rounded border border-[#3E4929] bg-[#17191C] p-5 flex flex-col gap-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#24272D] pb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#18261F] border border-[#253D30] text-[#80B89A] flex items-center justify-center shrink-0">
                    <Globe className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-[14px] font-medium text-[#F3F4F6]">
                        Built-in Deterministic Website Contact Crawler
                      </h3>
                      <span className="font-mono text-[10px] bg-[#18261F] text-[#80B89A] border border-[#253D30] px-1.5 py-0.2 rounded flex items-center gap-1">
                        <Check className="w-3 h-3" /> 100% Free &amp; Built-in
                      </span>
                    </div>
                    <p className="text-[12px] text-[#727780] mt-0.5">
                      Autonomous crawler that extracts genuine <code className="font-mono text-[#D8E7A2]">mailto:</code> addresses and phone numbers from homepages, <code className="font-mono text-[#A0A5AD]">/contact</code>, and <code className="font-mono text-[#A0A5AD]">/about</code> pages.
                    </p>
                  </div>
                </div>
                <span className="font-mono text-[11px] text-[#80B89A] bg-[#18261F] px-2.5 py-0.5 rounded border border-[#253D30] self-start sm:self-auto shrink-0">
                  Active (No API Key Needed)
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                <div className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1">
                  <strong className="text-[#F3F4F6] flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#80B89A]" />
                    Live DNS MX Deliverability Verification
                  </strong>
                  <p className="text-[#727780] leading-relaxed">
                    Filters out image files, asset URLs, and unroutable demo domains. Automatically executes DNS MX record queries to confirm the target business domain has active mail exchange servers.
                  </p>
                </div>
                <div className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1">
                  <strong className="text-[#F3F4F6] flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5 text-[#D8E7A2]" />
                    Direct Phone &amp; WhatsApp Discovery
                  </strong>
                  <p className="text-[#727780] leading-relaxed">
                    Identifies published telephone numbers and formats them for 1-click Call and WhatsApp outreach directly from your prospect drawer and email drafts.
                  </p>
                </div>
              </div>
            </div>

            {/* Provider: Multi-Channel Deep Search Dorking (Zero-Website Pipeline) */}
            <div className="rounded border border-[#3E4929] bg-[#17191C] p-5 flex flex-col gap-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#24272D] pb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#22271B] border border-[#3E4929] text-[#D8E7A2] flex items-center justify-center shrink-0">
                    <Compass className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-[14px] font-medium text-[#F3F4F6]">
                        Multi-Channel Social &amp; Deep Search Dorking (Zero-Website Pipeline)
                      </h3>
                      <span className="font-mono text-[10px] bg-[#18261F] text-[#80B89A] border border-[#253D30] px-1.5 py-0.2 rounded flex items-center gap-1">
                        <Check className="w-3 h-3" /> 100% Free &amp; Built-in
                      </span>
                    </div>
                    <p className="text-[12px] text-[#727780] mt-0.5">
                      Autonomous intelligence pipeline designed specifically for local food, retail, and commercial businesses in India that don't own a custom <code className="font-mono text-[#D8E7A2]">.com</code> domain.
                    </p>
                  </div>
                </div>
                <span className="font-mono text-[11px] text-[#80B89A] bg-[#18261F] px-2.5 py-0.5 rounded border border-[#253D30] self-start sm:self-auto shrink-0">
                  Active (No API Key Needed)
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
                <div className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1">
                  <strong className="text-[#F3F4F6] flex items-center gap-1">
                    <Share2 className="w-3.5 h-3.5 text-[#91B7D8]" />
                    Facebook &amp; Instagram Storefronts
                  </strong>
                  <p className="text-[#727780] leading-relaxed">
                    Scrapes the public About / Contact tab on Facebook Business Pages and Instagram professional bio metadata to extract direct Gmail and Yahoo addresses.
                  </p>
                </div>

                <div className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1">
                  <strong className="text-[#F3F4F6] flex items-center gap-1">
                    <Search className="w-3.5 h-3.5 text-[#D8E7A2]" />
                    Search Engine Dorking
                  </strong>
                  <p className="text-[#727780] leading-relaxed">
                    Targets table booking notices, catering flyers, and party hall listings using Google and Bing search snippet extraction with live DNS MX deliverability checks.
                  </p>
                </div>

                <div className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1">
                  <strong className="text-[#F3F4F6] flex items-center gap-1">
                    <MessageSquare className="w-3.5 h-3.5 text-[#80B89A]" />
                    WhatsApp &amp; Directory Intel
                  </strong>
                  <p className="text-[#727780] leading-relaxed">
                    Queries mobile numbers alongside Gmail on Indian business directories (Justdial, Zomato, Swiggy) and verifies FSSAI license / GSTIN public disclosures.
                  </p>
                </div>
              </div>
            </div>

            {/* Provider 2: Hunter.io B2B Email Finder */}
            <div className={`rounded border p-5 flex flex-col gap-4 ${
              enrichmentStatus?.hunter?.is_configured
                ? 'bg-[#17191C] border-[#3E4929]'
                : 'bg-[#141618] border-[#2B2F36]'
            }`}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#24272D] pb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg border flex items-center justify-center shrink-0 ${
                    enrichmentStatus?.hunter?.is_configured
                      ? 'bg-[#18261F] border-[#253D30] text-[#80B89A]'
                      : 'bg-[#1D2024] border-[#30343A] text-[#727780]'
                  }`}>
                    <Search className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-[14px] font-medium text-[#F3F4F6]">
                        Hunter.io Professional B2B Email Finder
                      </h3>
                      {enrichmentStatus?.hunter?.is_configured && (
                        <span className="font-mono text-[10px] bg-[#18261F] text-[#80B89A] border border-[#253D30] px-1.5 py-0.2 rounded flex items-center gap-1">
                          <Check className="w-3 h-3" /> Configured
                        </span>
                      )}
                    </div>
                    <p className="text-[12px] text-[#727780] mt-0.5">
                      Searches verified corporate domain email patterns with confidence scores, executive full names, and positions. Free tier includes 25 searches/month.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="secondary"
                    size="sm"
                    isLoading={isTestingHunter}
                    onClick={handleTestHunter}
                    leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                  >
                    Test API Connection
                  </Button>
                </div>
              </div>

              {/* API Key Input Row */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111214] p-3 rounded border border-[#24272D]">
                <div className="flex items-center gap-2 text-[12px]">
                  <Key className="w-4 h-4 text-[#D8E7A2]" />
                  <span className="text-[#A0A5AD] font-medium">API Key:</span>
                  {enrichmentStatus?.hunter?.masked_key ? (
                    <span className="font-mono text-[#F3F4F6] bg-[#1A1C20] px-2 py-0.5 rounded border border-[#30343A] text-[11px]">
                      {enrichmentStatus.hunter.masked_key}
                    </span>
                  ) : (
                    <span className="text-[#727780] italic text-[11px]">Not configured</span>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-1 sm:max-w-md">
                  <div className="relative flex-1">
                    <input
                      type={showHunterKey ? 'text' : 'password'}
                      value={hunterKey}
                      onChange={(e) => setHunterKey(e.target.value)}
                      placeholder="Insert Hunter.io API key..."
                      className="w-full bg-[#17191C] border border-[#2B2F36] rounded px-3 py-1.5 text-[12px] font-mono text-[#F3F4F6] focus:outline-none focus:border-[#D8E7A2] pr-8"
                    />
                    <button
                      type="button"
                      onClick={() => setShowHunterKey(!showHunterKey)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#727780] hover:text-[#F3F4F6]"
                    >
                      {showHunterKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    isLoading={isSavingHunter}
                    onClick={handleSaveHunterKey}
                    leftIcon={<Save className="w-3.5 h-3.5" />}
                    disabled={!hunterKey.trim()}
                  >
                    Save Key
                  </Button>
                </div>
              </div>

              {/* Hunter Test Result Banner */}
              {hunterTestResult && (
                <div className={`p-2.5 rounded border text-[11px] font-mono flex items-center justify-between ${
                  hunterTestResult.success
                    ? 'bg-[#18261F] border-[#253D30] text-[#80B89A]'
                    : 'bg-[#2A1818] border-[#4A2626] text-[#D78383]'
                }`}>
                  <div className="flex items-center gap-2">
                    {hunterTestResult.success ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                    <span>{hunterTestResult.message}</span>
                  </div>
                  {hunterTestResult.available_searches !== undefined && (
                    <span className="font-semibold">{hunterTestResult.available_searches} monthly searches remaining</span>
                  )}
                </div>
              )}

              {/* Developer Step-by-Step Setup Guide */}
              <div className="rounded bg-[#111214] border border-[#24272D] p-3.5 flex flex-col gap-2.5 text-[12px]">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-[#D8E7A2]">
                    How to Get Your Free Hunter.io API Key (25 Free Searches / Month)
                  </span>
                  <a
                    href="https://hunter.io/users/sign_up"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-[#91B7D8] hover:underline flex items-center gap-1 font-mono"
                  >
                    <span>Sign up at hunter.io</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[11px] text-[#A0A5AD]">
                  <div className="p-2 rounded bg-[#17191C] border border-[#262A30]">
                    <strong className="text-[#F3F4F6] block mb-0.5">1. Free Sign-Up</strong>
                    Register at <a href="https://hunter.io/users/sign_up" target="_blank" rel="noopener noreferrer" className="text-[#91B7D8] underline">hunter.io</a> using any business or personal email. No credit card required.
                  </div>
                  <div className="p-2 rounded bg-[#17191C] border border-[#262A30]">
                    <strong className="text-[#F3F4F6] block mb-0.5">2. Copy API Key</strong>
                    In your Hunter dashboard, click <strong className="text-[#F3F4F6]">API</strong> in the top menu and copy your private key.
                  </div>
                  <div className="p-2 rounded bg-[#17191C] border border-[#262A30]">
                    <strong className="text-[#F3F4F6] block mb-0.5">3. Paste &amp; Save</strong>
                    Paste the key above and click "Save Key", or add <code className="text-[#D8E7A2]">HUNTER_API_KEY="..."</code> to your local <code className="text-[#F3F4F6]">.env</code> file.
                  </div>
                </div>
              </div>
            </div>

            {/* Provider 3: Google Places API (New) */}
            <div className={`rounded border p-5 flex flex-col gap-4 ${
              enrichmentStatus?.google_places?.is_configured
                ? 'bg-[#17191C] border-[#3E4929]'
                : 'bg-[#141618] border-[#2B2F36]'
            }`}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#24272D] pb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg border flex items-center justify-center shrink-0 ${
                    enrichmentStatus?.google_places?.is_configured
                      ? 'bg-[#18261F] border-[#253D30] text-[#80B89A]'
                      : 'bg-[#1D2024] border-[#30343A] text-[#727780]'
                  }`}>
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-[14px] font-medium text-[#F3F4F6]">
                        Google Places API Gateway (Places API New)
                      </h3>
                      {enrichmentStatus?.google_places?.is_configured && (
                        <span className="font-mono text-[10px] bg-[#18261F] text-[#80B89A] border border-[#253D30] px-1.5 py-0.2 rounded flex items-center gap-1">
                          <Check className="w-3 h-3" /> Configured
                        </span>
                      )}
                    </div>
                    <p className="text-[12px] text-[#727780] mt-0.5">
                      Queries Google Maps Business Profiles to discover verified local phone numbers, official websites, operating hours, and customer reviews.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="secondary"
                    size="sm"
                    isLoading={isTestingPlaces}
                    onClick={handleTestPlaces}
                    leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                  >
                    Test Connection
                  </Button>
                </div>
              </div>

              {/* API Key Input Row */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111214] p-3 rounded border border-[#24272D]">
                <div className="flex items-center gap-2 text-[12px]">
                  <Key className="w-4 h-4 text-[#D8E7A2]" />
                  <span className="text-[#A0A5AD] font-medium">API Key:</span>
                  {enrichmentStatus?.google_places?.masked_key ? (
                    <span className="font-mono text-[#F3F4F6] bg-[#1A1C20] px-2 py-0.5 rounded border border-[#30343A] text-[11px]">
                      {enrichmentStatus.google_places.masked_key}
                    </span>
                  ) : (
                    <span className="text-[#727780] italic text-[11px]">Not configured</span>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-1 sm:max-w-md">
                  <div className="relative flex-1">
                    <input
                      type={showPlacesKey ? 'text' : 'password'}
                      value={placesKey}
                      onChange={(e) => setPlacesKey(e.target.value)}
                      placeholder="Insert Google Places API key (AIza...)"
                      className="w-full bg-[#17191C] border border-[#2B2F36] rounded px-3 py-1.5 text-[12px] font-mono text-[#F3F4F6] focus:outline-none focus:border-[#D8E7A2] pr-8"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPlacesKey(!showPlacesKey)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#727780] hover:text-[#F3F4F6]"
                    >
                      {showPlacesKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    isLoading={isSavingPlaces}
                    onClick={handleSavePlacesKey}
                    leftIcon={<Save className="w-3.5 h-3.5" />}
                    disabled={!placesKey.trim()}
                  >
                    Save Key
                  </Button>
                </div>
              </div>

              {/* Places Test Result Banner */}
              {placesTestResult && (
                <div className={`p-2.5 rounded border text-[11px] font-mono flex items-center justify-between ${
                  placesTestResult.success
                    ? 'bg-[#18261F] border-[#253D30] text-[#80B89A]'
                    : 'bg-[#2A1818] border-[#4A2626] text-[#D78383]'
                }`}>
                  <div className="flex items-center gap-2">
                    {placesTestResult.success ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                    <span>{placesTestResult.message}</span>
                  </div>
                </div>
              )}

              {/* Developer Step-by-Step Setup Guide */}
              <div className="rounded bg-[#111214] border border-[#24272D] p-3.5 flex flex-col gap-2.5 text-[12px]">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-[#D8E7A2]">
                    How to Get Your Google Places API Key ($200 Free Monthly Credit)
                  </span>
                  <a
                    href="https://console.cloud.google.com/apis/library/places.googleapis.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-[#91B7D8] hover:underline flex items-center gap-1 font-mono"
                  >
                    <span>Google Cloud Console</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-2 text-[11px] text-[#A0A5AD]">
                  <div className="p-2 rounded bg-[#17191C] border border-[#262A30]">
                    <strong className="text-[#F3F4F6] block mb-0.5">1. Open Cloud Console</strong>
                    Visit <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer" className="text-[#91B7D8] underline">console.cloud.google.com</a> and create or select your project.
                  </div>
                  <div className="p-2 rounded bg-[#17191C] border border-[#262A30]">
                    <strong className="text-[#F3F4F6] block mb-0.5">2. Enable Places API</strong>
                    Go to <strong className="text-[#F3F4F6]">APIs &amp; Services &gt; Library</strong>, search for <strong className="text-[#D8E7A2]">Places API (New)</strong> and click Enable.
                  </div>
                  <div className="p-2 rounded bg-[#17191C] border border-[#262A30]">
                    <strong className="text-[#F3F4F6] block mb-0.5">3. Create Credentials</strong>
                    Go to <strong className="text-[#F3F4F6]">Credentials &gt; Create Credentials &gt; API Key</strong>. Google grants $200 free monthly credit covering thousands of searches.
                  </div>
                  <div className="p-2 rounded bg-[#17191C] border border-[#262A30]">
                    <strong className="text-[#F3F4F6] block mb-0.5">4. Save Locally</strong>
                    Paste the key above and click Save Key, or write <code className="text-[#D8E7A2]">GOOGLE_PLACES_API_KEY="..."</code> to your <code className="text-[#F3F4F6]">.env</code>.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>


        {/* Section 5: Geographic Discovery Providers */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-[#D8B16C]" />
            <h2 className="text-[15px] font-semibold text-[#F3F4F6]">
              Geographic Discovery Providers
            </h2>
          </div>

          <div className="rounded border border-[#2B2F36] bg-[#17191C] p-5 flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-[#24272D] pb-3">
              <div>
                <h3 className="text-[14px] font-medium text-[#F3F4F6]">OpenStreetMap Overpass Engine</h3>
                <p className="text-[12px] text-[#727780]">Open-source geospatial commercial entity lookup</p>
              </div>
              <span className="font-mono text-[11px] text-[#80B89A] bg-[#18261F] px-2 py-0.5 rounded border border-[#253D30]">
                Active (Free Public Endpoint)
              </span>
            </div>

            <div className="flex items-center justify-between text-[12px] text-[#727780]">
              <span>Monthly request usage: <strong className="font-mono text-[#F3F4F6]">600 / 10,000</strong></span>
              <span>Endpoint: <code className="font-mono text-[#A0A5AD]">https://overpass-api.de/api/interpreter</code></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
