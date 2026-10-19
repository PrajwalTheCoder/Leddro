import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Search,
  Plus,
  UploadCloud,
  Compass,
  ExternalLink,
  FileText,
  Mail,
  Play,
  AlertTriangle,
  CheckCircle2,
  X,
  ChevronRight,
  ShieldCheck,
  Globe,
  SlidersHorizontal,
  ArrowUpDown,
  Lock,
  Layers,
  Sparkles,
  Timer,
  Terminal,
  Activity,
  History,
  TrendingUp,
  Copy,
  Check,
  Minus,
  Maximize2,
  AlertCircle,
  Radio,
  Send
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { ImportModal } from '../components/common/ImportModal';
import { NewProspectModal } from '../components/common/NewProspectModal';
import { GenerateDraftModal } from '../components/common/GenerateDraftModal';
import { TacticalGraphRadar } from '../components/dashboard/TacticalGraphRadar';

export const Overview: React.FC = () => {
  const {
    prospects,
    selectedProspectId,
    selectedProspect,
    setSelectedProspectId,
    runAudit,
    isAuditing,
    auditingProspectId,
    auditProgressMessage,
    auditReports,
    filterQuery,
    setFilterQuery,
    googleStatus
  } = useApp();

  const navigate = useNavigate();
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isNewProspectModalOpen, setIsNewProspectModalOpen] = useState(false);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [generateTargetId, setGenerateTargetId] = useState<string | null>(null);

  // Tactical Dashboard State (Image 1 Controls)
  type DashboardFilter = 'all' | 'active' | 'needs_review' | 'draft_ready' | 'offline' | 'high_priority';
  const [dashboardFilter, setDashboardFilter] = useState<DashboardFilter>('all');
  const [showLogs, setShowLogs] = useState(true);
  const [liveRadar, setLiveRadar] = useState(true);
  const [showInspectorCard, setShowInspectorCard] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [copiedTerminal, setCopiedTerminal] = useState(false);
  const [sortBy, setSortBy] = useState<'score' | 'name' | 'activity'>('score');
  const [sortAsc, setSortAsc] = useState(false);

  // Active target prospect (defaults to selected or first prospect in array)
  const activeTarget = selectedProspect || prospects[0];

  const selectedAudit = activeTarget?.latestAuditId
    ? auditReports[activeTarget.latestAuditId]
    : undefined;

  // Filter prospects
  const filteredProspects = useMemo(() => {
    return prospects.filter((p) => {
      // Search
      const matchesSearch =
        p.name.toLowerCase().includes(filterQuery.toLowerCase()) ||
        p.category.toLowerCase().includes(filterQuery.toLowerCase()) ||
        p.location.city.toLowerCase().includes(filterQuery.toLowerCase()) ||
        (p.websiteUrl && p.websiteUrl.toLowerCase().includes(filterQuery.toLowerCase()));
      if (!matchesSearch) return false;

      // Category
      if (categoryFilter !== 'all' && p.category.toLowerCase() !== categoryFilter.toLowerCase()) {
        return false;
      }

      // Filter pills from Image 1
      if (dashboardFilter === 'active') return p.auditCount > 0;
      if (dashboardFilter === 'needs_review') return p.status === 'needs_review';
      if (dashboardFilter === 'draft_ready') return p.status === 'draft_ready';
      if (dashboardFilter === 'offline') return ['unreachable', 'dns_error', 'ssl_expired'].includes(p.websiteStatus);
      if (dashboardFilter === 'high_priority') return p.opportunityScore >= 80;

      return true;
    }).sort((a, b) => {
      if (sortBy === 'score') {
        return sortAsc ? a.opportunityScore - b.opportunityScore : b.opportunityScore - a.opportunityScore;
      }
      if (sortBy === 'name') {
        return sortAsc ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
      }
      return 0;
    });
  }, [prospects, filterQuery, categoryFilter, dashboardFilter, sortBy, sortAsc]);

  // Derived metrics matching Image 1
  const totalCount = prospects.length;
  const auditedCount = prospects.filter((p) => p.auditCount > 0).length;
  const reviewCount = prospects.filter((p) => p.status === 'needs_review').length;
  const draftReadyCount = prospects.filter((p) => p.status === 'draft_ready').length;
  const offlineCount = prospects.filter((p) => ['unreachable', 'dns_error', 'ssl_expired'].includes(p.websiteStatus)).length;
  const auditCoveragePercent = totalCount > 0 ? Math.round((auditedCount / totalCount) * 100) : 0;

  // Handlers
  const handleAuditClick = async (prospectId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    await runAudit(prospectId);
  };

  const handleCreateDraftClick = (prospectId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setSelectedProspectId(prospectId);
    setGenerateTargetId(prospectId);
    setIsGenerateModalOpen(true);
  };

  const handleCopyTerminal = () => {
    const rawText = `// Raw HTTP socket inspection\n> GET /contact HTTP/1.1 → 404 Not Found\nServer: nginx/1.18.0 (Ubuntu)\nContent-Type: text/html; charset=UTF-8\nX-Frame-Options: SAMEORIGIN\nStrict-Transport-Security: max-age=0\n> Response checksum: 0x9AF83E12\nHost: ${activeTarget?.websiteUrl ? activeTarget.websiteUrl.replace(/https?:\/\//, '') : 'localhost'}`;
    navigator.clipboard.writeText(rawText);
    setCopiedTerminal(true);
    setTimeout(() => setCopiedTerminal(false), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-[#0D1017] text-[#F3F4F6] selection:bg-[#D2F824] selection:text-black">
      <div className="max-w-[1520px] w-full mx-auto px-5 lg:px-7 pt-5 pb-12">

        {/* PAGE TITLE & LIVE STATUS HEADER */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl lg:text-[26px] font-bold tracking-tight text-white font-sans">
                Operations Dashboard
              </h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-[#D2F824]/10 text-[#D2F824] border border-[#D2F824]/30 font-medium">
                v1.4 LIVE
              </span>
            </div>
            <p className="text-xs text-[#8B949E] font-mono mt-1 flex items-center gap-2">
              <span>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
              <span className="text-[#586274]">•</span>
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Real-time local intelligence &amp; audit matrix
              </span>
            </p>
          </div>

          {/* Action cluster */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="h-8 px-3 rounded-lg bg-[#161A23] border border-[#262D3D] text-xs text-[#F3F4F6] hover:border-[#D2F824]/40 flex items-center gap-1.5 font-medium transition-colors"
            >
              <UploadCloud className="w-4 h-4 text-[#D2F824]" />
              <span>Import CSV</span>
            </button>
            <button
              onClick={() => setIsNewProspectModalOpen(true)}
              className="h-8 px-3 rounded-lg bg-[#161A23] border border-[#262D3D] text-xs text-[#8B949E] hover:text-white flex items-center gap-1.5 font-mono transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Target</span>
            </button>
            <button
              onClick={() => navigate('/discover')}
              className="h-8 px-3.5 rounded-lg bg-[#D2F824] text-black font-semibold text-xs flex items-center gap-1.5 hover:bg-[#bce018] shadow-[0_0_12px_rgba(210,248,36,0.25)] transition-all"
            >
              <Compass className="w-4 h-4" />
              <span>Discover Prospects</span>
            </button>
          </div>
        </div>

        {/* FILTER PILLS BAR & REAL-TIME TOGGLES (Matching Image 1) */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-2 rounded-xl bg-[#161A23] border border-[#262D3D] mb-6 shadow-md">
          {/* Filter Pills List */}
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-0.5">
            <button
              onClick={() => setDashboardFilter('all')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${dashboardFilter === 'all'
                  ? 'bg-[#232938] border border-[#D2F824]/40 text-white shadow-[0_0_10px_rgba(210,248,36,0.1)]'
                  : 'text-[#8B949E] hover:text-white hover:bg-[#1C212D]'
                }`}
            >
              <span>All</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold ${dashboardFilter === 'all' ? 'bg-[#D2F824] text-black' : 'bg-[#1C212D] text-[#8B949E]'
                }`}>
                {totalCount}
              </span>
            </button>

            <button
              onClick={() => setDashboardFilter('active')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${dashboardFilter === 'active'
                  ? 'bg-[#232938] border border-[#D2F824]/40 text-white shadow-[0_0_10px_rgba(210,248,36,0.1)]'
                  : 'text-[#8B949E] hover:text-white hover:bg-[#1C212D]'
                }`}
            >
              <span>Active</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-[#1C212D] text-[#8B949E]">
                {auditedCount}
              </span>
            </button>

            <button
              onClick={() => setDashboardFilter('needs_review')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${dashboardFilter === 'needs_review'
                  ? 'bg-[#232938] border border-[#D2F824]/40 text-white shadow-[0_0_10px_rgba(210,248,36,0.1)]'
                  : 'text-[#8B949E] hover:text-white hover:bg-[#1C212D]'
                }`}
            >
              <span>Needs Review</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-[#1C212D] text-amber-400">
                {reviewCount}
              </span>
            </button>

            <button
              onClick={() => setDashboardFilter('draft_ready')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${dashboardFilter === 'draft_ready'
                  ? 'bg-[#232938] border border-[#D2F824]/40 text-white shadow-[0_0_10px_rgba(210,248,36,0.1)]'
                  : 'text-[#8B949E] hover:text-white hover:bg-[#1C212D]'
                }`}
            >
              <span>Draft Ready</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-[#1C212D] text-emerald-400">
                {draftReadyCount}
              </span>
            </button>

            <button
              onClick={() => setDashboardFilter('offline')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${dashboardFilter === 'offline'
                  ? 'bg-[#232938] border border-[#D2F824]/40 text-white shadow-[0_0_10px_rgba(210,248,36,0.1)]'
                  : 'text-[#8B949E] hover:text-white hover:bg-[#1C212D]'
                }`}
            >
              <span>Offline</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-[#1C212D] text-[#586274]">
                {offlineCount}
              </span>
            </button>

            {/* Tune Icon */}
            <button
              onClick={() => setDashboardFilter(dashboardFilter === 'high_priority' ? 'all' : 'high_priority')}
              className={`w-8 h-8 rounded-lg flex items-center justify-center border border-[#262D3D] ml-1 transition-colors ${dashboardFilter === 'high_priority' ? 'bg-[#232938] text-[#D2F824] border-[#D2F824]/40' : 'text-[#8B949E] hover:text-white hover:bg-[#1C212D]'
                }`}
              title="Filter Score ≥ 80"
            >
              <SlidersHorizontal className="w-4 h-4" />
            </button>
          </div>

          {/* Right Side Tactical Toggles (Matching Image 3) */}
          <div className="flex items-center gap-4 text-xs font-mono text-[#8B949E] px-2">
            {/* Toggle 1: Show Diagnostic Logs */}
            <div className="inline-flex items-center gap-2.5 select-none">
              <span
                className="cursor-pointer hover:text-white transition-colors"
                onClick={() => setShowLogs(!showLogs)}
              >
                Show logs
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={showLogs}
                onClick={() => setShowLogs(!showLogs)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none ${showLogs ? 'bg-[#D2F824]' : 'bg-[#232938]'
                  }`}
              >
                <span
                  className={`pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full shadow transition duration-200 ease-in-out mt-[3px] ${showLogs ? 'translate-x-[18px] bg-black' : 'translate-x-[3px] bg-white'
                    }`}
                />
              </button>
            </div>

            {/* Toggle 2: Real-time Radar */}
            <div className="inline-flex items-center gap-2.5 select-none border-l border-[#262D3D] pl-4">
              <span
                className="flex items-center gap-1 cursor-pointer hover:text-white transition-colors"
                onClick={() => setLiveRadar(!liveRadar)}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${liveRadar ? 'bg-emerald-400 animate-pulse' : 'bg-[#586274]'}`}></span>
                Live radar
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={liveRadar}
                onClick={() => setLiveRadar(!liveRadar)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none ${liveRadar ? 'bg-[#D2F824]' : 'bg-[#232938]'
                  }`}
              >
                <span
                  className={`pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full shadow transition duration-200 ease-in-out mt-[3px] ${liveRadar ? 'translate-x-[18px] bg-black' : 'translate-x-[3px] bg-white'
                    }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* TACTICAL COMMAND CENTER: RADAR & ACTIVE INSPECTOR TELEMETRY (Image 1 Canvas) */}
        <section className="mb-6 rounded-2xl bg-[#161A23] border border-[#262D3D] overflow-hidden relative shadow-2xl">
          {/* Butter-Smooth Force-Directed Radar Matrix & MiroFish Knowledge Graph Canvas */}
          <TacticalGraphRadar
            prospects={filteredProspects}
            activeTarget={activeTarget}
            onSelectProspect={(id) => setSelectedProspectId(id)}
            onRunAudit={handleAuditClick}
            onCreateDraft={(id, e) => {
              if (activeTarget && activeTarget.status === 'contacted') {
                navigate('/drafts');
              } else {
                handleCreateDraftClick(id, e);
              }
            }}
            isAuditing={isAuditing}
            auditingProspectId={auditingProspectId}
            googleStatus={googleStatus}
            liveRadar={liveRadar}
            showInspectorCard={showInspectorCard}
            setShowInspectorCard={setShowInspectorCard}
          />

          {/* REAL-TIME DIAGNOSTIC INSPECTOR PROBE (When Show Logs is ON) */}
          {showLogs && (
            <div className="border-t border-[#262D3D] bg-[#121620] p-4 animate-in fade-in duration-200">
              <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-[#262D3D]">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-[#D2F824]" />
                  <span className="text-xs font-bold text-white font-sans uppercase tracking-wider">
                    Diagnostic Inspector Probe
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                    <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse"></span>
                    REAL-TIME TELEMETRY
                  </span>
                </div>
                <button
                  onClick={handleCopyTerminal}
                  className="text-[10px] font-mono text-[#D2F824] hover:underline flex items-center gap-1"
                >
                  {copiedTerminal ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedTerminal ? 'Copied' : 'Copy Header'}</span>
                </button>
              </div>

              {/* Terminal Output */}
              <div className="p-3 bg-[#090C11] border border-[#262D3D] rounded-lg font-mono text-[11px] space-y-1 overflow-x-auto text-[#8B949E]">
                <p className="text-[#586274]">// Raw HTTP socket inspection • Live target stream</p>
                <p className={`font-semibold ${activeTarget?.websiteStatus === 'broken_pages'
                    ? 'text-rose-400'
                    : activeTarget?.websiteStatus === 'ssl_expired'
                      ? 'text-amber-400'
                      : activeTarget?.websiteStatus === 'unreachable'
                        ? 'text-rose-500'
                        : 'text-emerald-400'
                  }`}>
                  &gt; GET /contact HTTP/1.1 → {
                    activeTarget?.websiteStatus === 'broken_pages'
                      ? '404 Not Found'
                      : activeTarget?.websiteStatus === 'ssl_expired'
                        ? '200 OK (TLS Certificate Expired)'
                        : activeTarget?.websiteStatus === 'unreachable'
                          ? '503 Service Unavailable'
                          : '200 OK'
                  }
                </p>
                <p className="text-white">Server: nginx/1.18.0 (Ubuntu)</p>
                <p className="text-white">Content-Type: text/html; charset=UTF-8</p>
                <p className={activeTarget?.websiteStatus === 'ssl_expired' ? 'text-amber-400' : 'text-emerald-400'}>
                  X-Frame-Options: SAMEORIGIN
                </p>
                <p className={activeTarget?.websiteStatus === 'ssl_expired' ? 'text-rose-400' : 'text-emerald-400'}>
                  Strict-Transport-Security: {activeTarget?.websiteStatus === 'ssl_expired' ? 'max-age=0' : 'max-age=31536000; includeSubDomains'}
                </p>
                <p className="text-[#586274]">&gt; Response checksum: 0x9AF83E12</p>
              </div>

              <div className="mt-2.5 flex items-center justify-between text-[11px] font-mono text-[#8B949E]">
                <span className="truncate max-w-[280px]">
                  Host: <span className="text-white">{activeTarget?.websiteUrl ? activeTarget.websiteUrl.replace(/https?:\/\//, '') : 'localhost'}</span>
                </span>
                <span className="text-[#D2F824] font-bold">Latency: 73ms</span>
              </div>
            </div>
          )}
        </section>

        {/* 4 ELEVATED METRIC TELEMETRY CARDS (Image 1 Match) */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Metric 1: Total Prospects */}
          <div className="bg-[#161A23] border border-[#262D3D] rounded-xl p-4 shadow-lg hover:border-[#D2F824]/40 transition-colors flex flex-col justify-between">
            <div className="flex items-center justify-between text-[#8B949E] text-xs font-mono mb-2">
              <span>Total prospects</span>
              <span className="w-7 h-7 rounded-lg bg-[#1C212D] flex items-center justify-center text-white">
                <Building2 className="w-4 h-4" />
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-2xl font-bold font-mono text-white">{totalCount}</span>
              <span className="text-[11px] font-mono text-[#D2F824] bg-[#D2F824]/10 border border-[#D2F824]/30 px-2 py-0.5 rounded-md flex items-center gap-1 font-semibold">
                <TrendingUp className="w-3 h-3" /> +4 this week
              </span>
            </div>
          </div>

          {/* Metric 2: Audits Completed */}
          <div className="bg-[#161A23] border border-[#262D3D] rounded-xl p-4 shadow-lg hover:border-[#D2F824]/40 transition-colors flex flex-col justify-between">
            <div className="flex items-center justify-between text-[#8B949E] text-xs font-mono mb-2">
              <span>Audits completed</span>
              <span className="w-7 h-7 rounded-lg bg-[#1C212D] flex items-center justify-center text-[#D2F824]">
                <ShieldCheck className="w-4 h-4" />
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-2xl font-bold font-mono text-white">{auditedCount}</span>
              <span className="text-[11px] font-mono text-blue-400 bg-blue-500/10 border border-blue-500/30 px-2 py-0.5 rounded-md font-semibold">
                {auditCoveragePercent}% coverage
              </span>
            </div>
          </div>

          {/* Metric 3: Ready to review */}
          <div className="bg-[#161A23] border border-[#262D3D] rounded-xl p-4 shadow-lg hover:border-[#D2F824]/40 transition-colors flex flex-col justify-between">
            <div className="flex items-center justify-between text-[#8B949E] text-xs font-mono mb-2">
              <span>Ready to review</span>
              <span className="w-7 h-7 rounded-lg bg-[#1C212D] flex items-center justify-center text-amber-400">
                <AlertCircle className="w-4 h-4" />
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-2xl font-bold font-mono text-white">{reviewCount}</span>
              <span className="text-[11px] font-mono text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-md font-semibold">
                Actionable findings
              </span>
            </div>
          </div>

          {/* Metric 4: Outreach Logged */}
          <div className="bg-[#161A23] border border-[#262D3D] rounded-xl p-4 shadow-lg hover:border-[#D2F824]/40 transition-colors flex flex-col justify-between">
            <div className="flex items-center justify-between text-[#8B949E] text-xs font-mono mb-2">
              <span>Awaiting follow-up</span>
              <span className="w-7 h-7 rounded-lg bg-[#1C212D] flex items-center justify-center text-emerald-400">
                <Mail className="w-4 h-4" />
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-2xl font-bold font-mono text-white">{draftReadyCount}</span>
              <span className="text-[11px] font-mono text-[#8B949E] bg-[#1C212D] border border-[#262D3D] px-2 py-0.5 rounded-md">
                Outreach logged
              </span>
            </div>
          </div>
        </section>

        {/* TWO COLUMN WORKSPACE (Table + Timeline Activity & Terminal Probe) */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          {/* LEFT 8-COLS: SLEEK RECENT PROSPECTS TABLE */}
          <section className="xl:col-span-8 bg-[#161A23] border border-[#262D3D] rounded-xl shadow-xl overflow-hidden">
            {/* Table Controls Header */}
            <div className="p-4 border-b border-[#262D3D] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[#161A23]/70">
              <div className="flex items-center gap-3">
                <h2 className="text-sm font-bold text-white font-sans uppercase tracking-wider flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#D2F824]"></span>
                  Recent Prospects
                </h2>
                <span className="text-[11px] font-mono text-[#8B949E] bg-[#1C212D] border border-[#262D3D] px-2 py-0.5 rounded">
                  {filteredProspects.length} active
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {/* Search filter input */}
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#586274]" />
                  <input
                    type="text"
                    value={filterQuery}
                    onChange={(e) => setFilterQuery(e.target.value)}
                    placeholder="Filter table..."
                    className="h-8 pl-8 pr-2.5 text-xs font-mono bg-[#1C212D] border border-[#262D3D] rounded-lg text-white placeholder:text-[#586274] focus:outline-none focus:border-[#D2F824]/60 w-36 sm:w-44 transition-colors"
                  />
                </div>

                {/* Status Dropdown */}
                <select
                  value={dashboardFilter}
                  onChange={(e) => setDashboardFilter(e.target.value as any)}
                  className="h-8 pl-2 pr-6 text-xs font-mono bg-[#1C212D] border border-[#262D3D] rounded-lg text-[#8B949E] focus:outline-none focus:border-[#D2F824]/60"
                >
                  <option value="all">All Statuses</option>
                  <option value="needs_review">Needs Review</option>
                  <option value="draft_ready">Draft Ready</option>
                  <option value="active">Audited</option>
                  <option value="offline">Offline</option>
                </select>

                {/* Category Dropdown */}
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="h-8 pl-2 pr-6 text-xs font-mono bg-[#1C212D] border border-[#262D3D] rounded-lg text-[#8B949E] focus:outline-none focus:border-[#D2F824]/60"
                >
                  <option value="all">All Categories</option>
                  <option value="interior design">Interior Design</option>
                  <option value="manufacturing">Manufacturing</option>
                  <option value="architecture">Architecture</option>
                  <option value="machining & tooling">Machining & Tooling</option>
                  <option value="logistics">Logistics</option>
                </select>
              </div>
            </div>

            {/* Table Viewport */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#1C212D]/80 border-b border-[#262D3D] text-[11px] font-mono text-[#8B949E] uppercase tracking-wider">
                    <th className="py-3 px-4 font-semibold">Business Name &amp; Category</th>
                    <th className="py-3 px-4 font-semibold">Website &amp; Condition</th>
                    <th className="py-3 px-4 font-semibold">Score</th>
                    <th className="py-3 px-4 font-semibold">Status</th>
                    <th className="py-3 px-4 font-semibold">Last Activity</th>
                    <th className="py-3 px-4 font-semibold text-right">Quick Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#262D3D] text-xs font-mono">
                  {filteredProspects.map((p) => {
                    const isSelected = activeTarget?.id === p.id;
                    const isRowAuditing = isAuditing && auditingProspectId === p.id;

                    return (
                      <tr
                        key={p.id}
                        onClick={() => {
                          setSelectedProspectId(p.id);
                          setShowInspectorCard(true);
                        }}
                        className={`transition-colors cursor-pointer ${isSelected
                            ? 'bg-[#1C212D]/60 border-l-2 border-l-[#D2F824]'
                            : 'hover:bg-[#1C212D]/40'
                          }`}
                      >
                        <td className="py-3.5 px-4">
                          <div className="flex flex-col">
                            <div className="flex items-center gap-1.5">
                              <span className="font-sans font-semibold text-white text-sm">{p.name}</span>
                              {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-[#D2F824]"></span>}
                            </div>
                            <span className="text-[11px] text-[#8B949E] font-mono">
                              {p.category} • {p.location.city}
                            </span>
                          </div>
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="flex flex-col">
                            {p.websiteUrl ? (
                              <>
                                <span className="text-[#D2F824] font-medium truncate max-w-xs">
                                  {p.websiteUrl.replace(/https?:\/\//, '')}
                                </span>
                                {p.websiteStatus === 'broken_pages' && (
                                  <span className="text-[11px] text-rose-400 flex items-center gap-1">
                                    <AlertTriangle className="w-3 h-3" /> HTTP 404 contact page
                                  </span>
                                )}
                                {p.websiteStatus === 'ssl_expired' && (
                                  <span className="text-[11px] text-rose-400 flex items-center gap-1">
                                    <Lock className="w-3 h-3" /> SSL expiring soon
                                  </span>
                                )}
                              </>
                            ) : (
                              <div className="flex items-center gap-1.5 text-[#8B949E] text-[11px]">
                                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                                <span className="italic">Website: Not listed (Requires verification)</span>
                              </div>
                            )}
                          </div>
                        </td>

                        <td className="py-3.5 px-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${p.opportunityScore >= 80
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            }`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${p.opportunityScore >= 80 ? 'bg-rose-500' : 'bg-amber-400'}`}></span>
                            {p.opportunityScore}/100
                          </span>
                        </td>

                        <td className="py-3.5 px-4">
                          <Badge variant="status" prospectStatus={p.status} size="sm" />
                        </td>

                        <td className="py-3.5 px-4 text-[#586274] text-[11px]">
                          {p.lastActivity}
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          <div className="inline-flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={(e) => handleAuditClick(p.id, e)}
                              disabled={isAuditing}
                              className="px-2.5 py-1 rounded bg-[#1C212D] border border-[#262D3D] text-[11px] text-[#F3F4F6] hover:text-white hover:border-[#8B949E] transition-colors disabled:opacity-40"
                            >
                              {isRowAuditing ? 'Auditing...' : p.auditCount > 0 ? 'Re-Audit' : 'Audit'}
                            </button>
                            <button
                              onClick={(e) => handleCreateDraftClick(p.id, e)}
                              className="px-2.5 py-1 rounded bg-[#D2F824] text-black font-semibold text-[11px] hover:bg-[#bce018] transition-colors"
                            >
                              Draft Email
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}

                  {filteredProspects.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-[#8B949E]">
                        <Building2 className="w-8 h-8 text-[#262D3D] mx-auto mb-2" />
                        <div className="text-sm">No prospects match the selected filter.</div>
                        <button
                          onClick={() => { setDashboardFilter('all'); setFilterQuery(''); setCategoryFilter('all'); }}
                          className="mt-2 text-xs text-[#D2F824] hover:underline"
                        >
                          Reset Filters
                        </button>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Table Footer */}
            <div className="px-4 py-3 border-t border-[#262D3D] bg-[#1C212D]/40 flex items-center justify-between text-xs font-mono text-[#8B949E]">
              <span>Showing {filteredProspects.length} of {totalCount} total entries</span>
              <div className="flex items-center gap-1">
                <button className="px-2.5 py-1 rounded bg-[#D2F824] text-black font-bold text-[11px]">1</button>
                <button className="px-2.5 py-1 rounded border border-[#262D3D] hover:bg-[#1C212D] text-white text-[11px]">2</button>
                <button className="px-2 py-1 rounded border border-[#262D3D] hover:bg-[#1C212D] text-[#F3F4F6] text-[11px]">Next</button>
              </div>
            </div>
          </section>

          {/* RIGHT 4-COLS: AUDIT ACTIVITY FEED & LIVE ENGINE TERMINAL PROBE */}
          <section className="xl:col-span-4 flex flex-col gap-6">
            {/* Activity Timeline Box */}
            <div className="bg-[#161A23] border border-[#262D3D] rounded-xl p-5 shadow-xl">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#262D3D]">
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-[#D2F824]" />
                  <h2 className="text-xs font-bold text-white font-sans uppercase tracking-wider">
                    Audit Activity Log
                  </h2>
                </div>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Live
                </span>
              </div>

              {/* Chronological Timeline */}
              <div className="relative pl-5 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-[1px] before:bg-[#262D3D]">
                <div className="relative">
                  <span className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-[#D2F824] shadow-[0_0_6px_#D2F824]"></span>
                  <div className="flex flex-col">
                    <span className="text-xs font-sans font-semibold text-white">
                      {activeTarget?.name || 'Harbor Furniture Works'} Audit
                    </span>
                    <p className="text-[11px] text-[#8B949E] font-sans mt-0.5">
                      Technical findings detected (Broken canonical URL, 404 route, uncompressed assets).
                    </p>
                    <span className="text-[10px] font-mono text-[#586274] mt-1">
                      Today at 14:22 • Engine 1.4
                    </span>
                  </div>
                </div>

                <div className="relative">
                  <span className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#10B981]"></span>
                  <div className="flex flex-col">
                    <span className="text-xs font-sans font-semibold text-white">
                      Local database backup synced
                    </span>
                    <p className="text-[11px] text-[#8B949E] font-sans mt-0.5">
                      WAL checkpoint complete. {totalCount} prospects &amp; audit reports committed.
                    </p>
                    <span className="text-[10px] font-mono text-[#586274] mt-1">
                      Today at 12:45 • SQLite WAL
                    </span>
                  </div>
                </div>

                <div className="relative">
                  <span className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-amber-400 shadow-[0_0_6px_#F59E0B]"></span>
                  <div className="flex flex-col">
                    <span className="text-xs font-sans font-semibold text-white">
                      Draft email prepared for {prospects[1]?.name || 'Willow Studio'}
                    </span>
                    <p className="text-[11px] text-[#8B949E] font-sans mt-0.5">
                      Subject: "Quick observation regarding mobile viewport on portfolio sub-routes"
                    </p>
                    <span className="text-[10px] font-mono text-[#586274] mt-1">
                      Yesterday at 17:10 • Pitch Engine
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

      {/* Modals */}
      <ImportModal isOpen={isImportModalOpen} onClose={() => setIsImportModalOpen(false)} />
      <NewProspectModal isOpen={isNewProspectModalOpen} onClose={() => setIsNewProspectModalOpen(false)} />
      <GenerateDraftModal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        targetProspectId={generateTargetId}
      />
    </div>
  );
};
