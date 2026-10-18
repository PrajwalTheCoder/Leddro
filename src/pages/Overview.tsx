import React, { useState, useMemo } from 'react';
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
  const [radarZoom, setRadarZoom] = useState(1);
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

  // Precomputed coordinates for Central Hub ("YOU") and orbiting target nodes
  const hubPos = { top: '50%', left: '50%', x: 50, y: 50 };

  const radarNodes = useMemo(() => {
    const defaultPositions = [
      { top: '50%', left: '68%', x: 68, y: 50 }, // East of hub (Apex Precision Tech)
      { top: '26%', left: '38%', x: 38, y: 26 }, // North-West of hub (Mintmorsel)
      { top: '74%', left: '78%', x: 78, y: 74 }, // South-East of hub (Kaveri Logistics)
      { top: '32%', left: '76%', x: 76, y: 32 }, // North-East of hub (Kanchan)
      { top: '68%', left: '34%', x: 34, y: 68 }, // South-West of hub (Sai Sagar)
      { top: '16%', left: '50%', x: 50, y: 16 }, // North of hub (Northstar Interiors)
    ];

    return prospects.slice(0, 6).map((p, idx) => {
      const pos = defaultPositions[idx % defaultPositions.length];
      const isSelected = activeTarget?.id === p.id;
      let colorType = 'lime';
      if (p.websiteStatus === 'ssl_expired' || p.websiteStatus === 'unreachable') {
        colorType = 'rose';
      } else if (p.websiteStatus === 'broken_pages' || p.status === 'needs_review') {
        colorType = 'amber';
      }
      return { ...p, pos, isSelected, colorType };
    });
  }, [prospects, activeTarget]);

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
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                dashboardFilter === 'all'
                  ? 'bg-[#232938] border border-[#D2F824]/40 text-white shadow-[0_0_10px_rgba(210,248,36,0.1)]'
                  : 'text-[#8B949E] hover:text-white hover:bg-[#1C212D]'
              }`}
            >
              <span>All</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold ${
                dashboardFilter === 'all' ? 'bg-[#D2F824] text-black' : 'bg-[#1C212D] text-[#8B949E]'
              }`}>
                {totalCount}
              </span>
            </button>

            <button
              onClick={() => setDashboardFilter('active')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                dashboardFilter === 'active'
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
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                dashboardFilter === 'needs_review'
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
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                dashboardFilter === 'draft_ready'
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
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                dashboardFilter === 'offline'
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
              className={`w-8 h-8 rounded-lg flex items-center justify-center border border-[#262D3D] ml-1 transition-colors ${
                dashboardFilter === 'high_priority' ? 'bg-[#232938] text-[#D2F824] border-[#D2F824]/40' : 'text-[#8B949E] hover:text-white hover:bg-[#1C212D]'
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
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none ${
                  showLogs ? 'bg-[#D2F824]' : 'bg-[#232938]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full shadow transition duration-200 ease-in-out mt-[3px] ${
                    showLogs ? 'translate-x-[18px] bg-black' : 'translate-x-[3px] bg-white'
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
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none ${
                  liveRadar ? 'bg-[#D2F824]' : 'bg-[#232938]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full shadow transition duration-200 ease-in-out mt-[3px] ${
                    liveRadar ? 'translate-x-[18px] bg-black' : 'translate-x-[3px] bg-white'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* TACTICAL COMMAND CENTER: RADAR & ACTIVE INSPECTOR TELEMETRY (Image 1 Canvas) */}
        <section className="mb-6 rounded-2xl bg-[#161A23] border border-[#262D3D] overflow-hidden relative shadow-2xl">
          {/* Interactive Radar / Diagnostic Map Canvas Area */}
          <div 
            className="relative w-full h-[410px] lg:h-[450px] bg-[#0A0D13] tactical-grid overflow-hidden transition-all duration-300"
            style={{ transform: `scale(${radarZoom})`, transformOrigin: 'center center' }}
          >
            {/* Compass / Orientation Rose (Top Right HUD Gizmo) */}
            <div className="absolute top-4 right-4 z-20 w-24 h-24 rounded-full bg-[#161A23]/90 border border-[#262D3D]/80 backdrop-blur-md flex items-center justify-center shadow-xl">
              <div className="relative w-20 h-20 rounded-full border border-dashed border-white/20 flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border border-[#D2F824]/20 animate-compass"></div>
                {/* Compass Needle */}
                <div className="flex flex-col items-center">
                  <span className="text-[11px] font-mono font-bold text-[#D2F824] tracking-widest">NW</span>
                  <div className="w-1 h-8 bg-gradient-to-b from-rose-500 via-amber-400 to-transparent rounded-full shadow-[0_0_8px_#f43f5e]"></div>
                  <span className="text-[8px] font-mono text-[#586274]">312°</span>
                </div>
                <span className="absolute top-1 text-[8px] font-mono text-[#8B949E]">N</span>
                <span className="absolute bottom-1 text-[8px] font-mono text-[#586274]">S</span>
                <span className="absolute right-1 text-[8px] font-mono text-[#586274]">E</span>
                <span className="absolute left-1 text-[8px] font-mono text-[#586274]">W</span>
              </div>
            </div>

            {/* Radar Sweep Ring & Coordinates in Center */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
              <div className="relative w-[520px] h-[520px] rounded-full border border-[#D2F824]/10 flex items-center justify-center">
                <div className="w-[360px] h-[360px] rounded-full border border-[#D2F824]/15"></div>
                <div className="w-[200px] h-[200px] rounded-full border border-[#D2F824]/20"></div>
                {liveRadar && (
                  <div className="absolute inset-0 rounded-full animate-radar bg-gradient-to-tr from-[#D2F824]/10 via-transparent to-transparent"></div>
                )}
              </div>
            </div>

            {/* Dynamic Reactive Network Vectors: Hub ("YOU") ↔ Prospects */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
              <defs>
                <filter id="glow-emerald" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glow-lime" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {radarNodes.map((node) => {
                const isContacted = node.status === 'contacted';
                const isDraftReady = node.status === 'draft_ready';
                const isSelected = activeTarget?.id === node.id;
                const isBeingAudited = isAuditing && auditingProspectId === node.id;

                const strokeColor = isSelected || isBeingAudited
                  ? '#D2F824'
                  : isContacted
                  ? '#10B981'
                  : isDraftReady
                  ? '#F59E0B'
                  : '#262D3D';

                const strokeWidth = isSelected || isContacted || isBeingAudited ? 2 : 1;
                const strokeDash = isDraftReady ? '4,4' : isContacted ? '5,5' : isSelected ? '0' : '2,3';
                const opacity = isContacted || isSelected || isDraftReady || isBeingAudited ? 0.85 : 0.25;

                return (
                  <g key={`vector-${node.id}`}>
                    {/* Glow halo for connected or selected links */}
                    {(isContacted || isSelected || isBeingAudited) && (
                      <line
                        x1={`${hubPos.x}%`}
                        y1={`${hubPos.y}%`}
                        x2={`${node.pos.x}%`}
                        y2={`${node.pos.y}%`}
                        stroke={strokeColor}
                        strokeWidth={5}
                        opacity={0.3}
                        filter={isContacted ? 'url(#glow-emerald)' : 'url(#glow-lime)'}
                      />
                    )}

                    {/* Primary Vector Beam */}
                    <line
                      x1={`${hubPos.x}%`}
                      y1={`${hubPos.y}%`}
                      x2={`${node.pos.x}%`}
                      y2={`${node.pos.y}%`}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      strokeDasharray={strokeDash}
                      opacity={opacity}
                    />
                  </g>
                );
              })}
            </svg>

            {/* CENTRAL HUB NODE: "YOU" / SENDER / OPERATOR (Gmail Gateway Beacon) */}
            <div
              style={{ top: hubPos.top, left: hubPos.left }}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-20 flex flex-col items-center group cursor-pointer"
              onClick={() => navigate('/integrations')}
              title="Click to view connected Gmail & AI integrations"
            >
              <div className="relative flex h-10 w-10 items-center justify-center">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-25"></span>
                <span className="absolute inline-flex h-8 w-8 rounded-full bg-gradient-to-tr from-emerald-500/30 to-[#D2F824]/20 border border-emerald-400/50 shadow-[0_0_15px_rgba(16,185,129,0.5)]"></span>
                <div className="relative inline-flex items-center justify-center rounded-full h-6 w-6 bg-[#0D1017] border border-emerald-400 text-emerald-400">
                  <Radio className="w-3.5 h-3.5 animate-pulse" />
                </div>
              </div>

              <div className="mt-1 px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-[#161A23]/95 border border-emerald-400/50 text-white shadow-xl flex items-center gap-1 whitespace-nowrap group-hover:border-emerald-300 transition-colors">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="text-emerald-400">YOU</span>
                <span className="text-[#8B949E] text-[8px] max-w-[110px] truncate">
                  ({googleStatus?.is_connected && googleStatus.email ? googleStatus.email : 'Leddro Hub'})
                </span>
              </div>
            </div>

            {/* Connection Status Badges Over Network Vector Midpoints */}
            {radarNodes.map((node) => {
              const midX = (hubPos.x + node.pos.x) / 2;
              const midY = (hubPos.y + node.pos.y) / 2;

              if (node.status === 'contacted') {
                return (
                  <div 
                    key={`badge-${node.id}`}
                    style={{ left: `${midX}%`, top: `${midY}%` }}
                    className="absolute -translate-x-1/2 -translate-y-1/2 z-10 pointer-events-none"
                  >
                    <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-[#0D1017]/95 border border-emerald-500/60 text-[8px] font-mono font-bold text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.35)] whitespace-nowrap">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                      CONNECTED • VIA GMAIL
                    </div>
                  </div>
                );
              }

              if (node.status === 'draft_ready') {
                return (
                  <div 
                    key={`badge-${node.id}`}
                    style={{ left: `${midX}%`, top: `${midY}%` }}
                    className="absolute -translate-x-1/2 -translate-y-1/2 z-10 pointer-events-none"
                  >
                    <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-[#0D1017]/95 border border-amber-500/60 text-[8px] font-mono font-bold text-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.3)] whitespace-nowrap">
                      DRAFT READY
                    </div>
                  </div>
                );
              }

              return null;
            })}

            {/* Pulsing Target Nodes on Map */}
            {radarNodes.map((node) => {
              const isSelected = activeTarget?.id === node.id;

              return (
                <div
                  key={node.id}
                  onClick={() => {
                    setSelectedProspectId(node.id);
                    setShowInspectorCard(true);
                  }}
                  style={{ top: node.pos.top, left: node.pos.left }}
                  className="absolute -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center cursor-pointer group transition-transform hover:scale-110"
                >
                  {isSelected ? (
                    <span className="relative flex h-8 w-8 items-center justify-center">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#D2F824] opacity-40"></span>
                      <span className="relative inline-flex rounded-full h-4 w-4 bg-[#D2F824] shadow-[0_0_12px_#D2F824]"></span>
                    </span>
                  ) : node.status === 'contacted' ? (
                    <span className="relative flex h-5 w-5 items-center justify-center">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-30"></span>
                      <span className="w-3.5 h-3.5 rounded-full bg-emerald-400 shadow-[0_0_10px_#10B981] opacity-90 group-hover:opacity-100"></span>
                    </span>
                  ) : node.colorType === 'rose' ? (
                    <span className="w-3.5 h-3.5 rounded-full bg-rose-500 shadow-[0_0_8px_#f43f5e] opacity-80 group-hover:opacity-100"></span>
                  ) : node.colorType === 'amber' ? (
                    <span className="w-3.5 h-3.5 rounded-full bg-amber-400 shadow-[0_0_8px_#f59e0b] opacity-80 group-hover:opacity-100"></span>
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full bg-[#D2F824] shadow-[0_0_8px_#D2F824] opacity-80 group-hover:opacity-100"></span>
                  )}

                  <div className={`mt-1 px-2 py-0.5 rounded text-[10px] font-mono whitespace-nowrap shadow-lg transition-all ${
                    isSelected
                      ? 'bg-[#1C212D]/95 border border-[#D2F824]/60 text-[#D2F824]'
                      : node.status === 'contacted'
                      ? 'bg-[#161A23]/90 border border-emerald-500/50 text-emerald-300'
                      : 'bg-[#161A23]/80 border border-[#262D3D] text-[#8B949E] group-hover:text-white'
                  }`}>
                    {node.websiteUrl ? node.websiteUrl.replace(/https?:\/\//, '') : node.name}
                    {node.status === 'contacted' && ' • Connected'}
                    {node.websiteStatus === 'broken_pages' && ' • 404 Route'}
                    {node.websiteStatus === 'ssl_expired' && ' • SSL Expiring'}
                  </div>
                </div>
              );
            })}

            {/* OVERLAID ACTIVE INSPECTION PANEL (Exact match from Image 1) */}
            {activeTarget && showInspectorCard && (
              <div className="absolute top-4 left-4 z-30 w-[92%] sm:w-[410px] bg-[#161A23]/95 backdrop-blur-xl border border-[#262D3D] rounded-xl p-4 shadow-2xl animate-in fade-in slide-in-from-left-2">
                {/* Header of card */}
                <div className="flex items-start justify-between pb-3 border-b border-[#262D3D]">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#1C212D] border border-[#262D3D] flex items-center justify-center text-[#D2F824]">
                      <Building2 className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white font-sans truncate max-w-[200px]">
                          {activeTarget.name}
                        </span>
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          {activeTarget.auditCount > 0 ? 'Live Audit' : 'Target'}
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-[#8B949E]">
                        {activeTarget.category} • {activeTarget.location.city}
                      </span>
                    </div>
                  </div>
                  <button 
                    onClick={() => setShowInspectorCard(false)}
                    className="text-[#586274] hover:text-white transition-colors" 
                    title="Dismiss card"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Network Relationship to US */}
                <div className="py-2.5 border-b border-[#262D3D]">
                  {activeTarget.status === 'contacted' ? (
                    <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs font-mono text-emerald-400">
                      <div className="flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span className="font-semibold">CONNECTED TO YOU</span>
                      </div>
                      <span className="text-[10px] text-emerald-300 font-mono">Sent via Gmail</span>
                    </div>
                  ) : activeTarget.status === 'draft_ready' ? (
                    <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-between text-xs font-mono text-amber-400">
                      <div className="flex items-center gap-1.5">
                        <Mail className="w-4 h-4 text-amber-400 shrink-0" />
                        <span className="font-semibold">DRAFT QUEUED</span>
                      </div>
                      <span className="text-[10px] text-amber-300 font-mono">Ready to Dispatch</span>
                    </div>
                  ) : (
                    <div className="p-2 rounded-lg bg-[#1C212D] border border-[#262D3D] flex items-center justify-between text-xs font-mono text-[#8B949E]">
                      <div className="flex items-center gap-1.5">
                        <Activity className="w-4 h-4 text-[#D2F824] shrink-0" />
                        <span>Recon Discovered</span>
                      </div>
                      <span className="text-[10px] text-[#586274]">Target Host Scanned</span>
                    </div>
                  )}
                </div>

                {/* Route / Audit Scope Progress Bar */}
                <div className="py-3 border-b border-[#262D3D]/60">
                  <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                    <span className="text-[#8B949E]">Target Host → Contact Form Path</span>
                    <span className={`font-semibold ${
                      activeTarget.websiteStatus === 'broken_pages' || activeTarget.websiteStatus === 'unreachable'
                        ? 'text-rose-400'
                        : activeTarget.websiteStatus === 'ssl_expired'
                        ? 'text-amber-400'
                        : 'text-[#D2F824]'
                    }`}>
                      {activeTarget.websiteStatus === 'broken_pages'
                        ? 'HTTP 404 Failure'
                        : activeTarget.websiteStatus === 'ssl_expired'
                        ? 'TLS Expiring'
                        : activeTarget.websiteStatus === 'unreachable'
                        ? 'Host Unreachable'
                        : '200 OK Active'}
                    </span>
                  </div>
                  <div className="w-full h-2 bg-[#1C212D] rounded-full overflow-hidden flex">
                    <div 
                      className="h-full bg-[#D2F824] rounded-full shadow-[0_0_8px_#D2F824]"
                      style={{ width: `${Math.min(activeTarget.opportunityScore, 85)}%` }}
                    ></div>
                    <div 
                      className="h-full bg-rose-500 rounded-r-full"
                      style={{ width: `${Math.max(100 - activeTarget.opportunityScore, 15)}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-between mt-2 text-[11px] font-mono text-[#586274]">
                    <span className="flex items-center gap-1 text-[#8B949E]">
                      <Timer className="w-3.5 h-3.5 text-[#D2F824]" /> Latency: ~73ms
                    </span>
                    <span>Crawled {activeTarget.auditCount * 6 + 12}/24 sub-routes</span>
                  </div>
                </div>

                {/* Two Dual Gauges (Exact Speedometer Match from Image 1) */}
                <div className="grid grid-cols-2 gap-3 pt-3">
                  {/* Gauge 1: Opportunity Score */}
                  <div className="p-2.5 rounded-lg bg-[#1C212D] border border-[#262D3D] flex flex-col items-center relative overflow-hidden">
                    <div className="w-full flex items-center justify-between text-[11px] font-mono text-[#8B949E] mb-1">
                      <span>Audit Score</span>
                      <span className={`px-1 py-0.2 rounded text-[9px] font-bold border ${
                        activeTarget.opportunityScore >= 80
                          ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                          : 'bg-[#D2F824]/20 text-[#D2F824] border-[#D2F824]/30'
                      }`}>
                        {activeTarget.opportunityScore >= 80 ? 'HIGH ROI' : 'ACTIONABLE'}
                      </span>
                    </div>
                    {/* Semi Gauge Ring SVG */}
                    <div className="relative w-24 h-24 flex items-center justify-center">
                      <svg className="w-24 h-24 -rotate-90">
                        <circle cx="48" cy="48" fill="transparent" r="38" stroke="#252B3B" strokeWidth="6"></circle>
                        <circle 
                          className="drop-shadow-[0_0_6px_rgba(210,248,36,0.5)] transition-all duration-700" 
                          cx="48" 
                          cy="48" 
                          fill="transparent" 
                          r="38" 
                          stroke="#D2F824" 
                          strokeDasharray="238" 
                          strokeDashoffset={238 - (238 * activeTarget.opportunityScore) / 100} 
                          strokeLinecap="round" 
                          strokeWidth="6"
                        ></circle>
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-lg font-mono font-bold text-white">
                          {activeTarget.opportunityScore}<span className="text-[11px] text-[#8B949E]">/100</span>
                        </span>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-[#D2F824] font-medium mt-0.5">
                      High pitch viability
                    </span>
                  </div>

                  {/* Gauge 2: Response & Assets Load */}
                  <div className="p-2.5 rounded-lg bg-[#1C212D] border border-[#262D3D] flex flex-col items-center relative overflow-hidden">
                    <div className="w-full flex items-center justify-between text-[11px] font-mono text-[#8B949E] mb-1">
                      <span>Server Latency</span>
                      <span className="px-1 py-0.2 rounded text-[9px] bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold">
                        {activeTarget.websiteStatus === 'active' ? 'OPTIMAL' : 'SLOW'}
                      </span>
                    </div>
                    {/* Radial Dial */}
                    <div className="relative w-24 h-24 flex items-center justify-center">
                      <svg className="w-24 h-24 -rotate-90">
                        <circle cx="48" cy="48" fill="transparent" r="38" stroke="#252B3B" strokeWidth="6"></circle>
                        <circle 
                          cx="48" 
                          cy="48" 
                          fill="transparent" 
                          r="38" 
                          stroke="#F59E0B" 
                          strokeDasharray="238" 
                          strokeDashoffset="110" 
                          strokeLinecap="round" 
                          strokeWidth="6"
                        ></circle>
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-lg font-mono font-bold text-white">
                          2.4<span className="text-[11px] text-[#8B949E]">s</span>
                        </span>
                        <span className="text-[9px] font-mono text-[#586274]">TTFB 73ms</span>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-amber-400 font-medium mt-0.5 truncate max-w-[140px]">
                      {activeTarget.websiteStatus === 'active' ? 'Clean headers' : '3 uncompressed images'}
                    </span>
                  </div>
                </div>

                {/* Card Bottom Tactical Warning Alert Banner */}
                <div className="mt-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-mono text-amber-300">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    <span className="truncate max-w-[220px]">
                      {activeTarget.recommendedAction}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button 
                      onClick={(e) => {
                        if (activeTarget.status === 'contacted') {
                          navigate('/drafts');
                        } else {
                          handleCreateDraftClick(activeTarget.id, e);
                        }
                      }}
                      className={`px-2.5 py-1 rounded font-semibold text-[10px] font-mono transition-colors flex items-center gap-1 ${
                        activeTarget.status === 'contacted'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30'
                          : activeTarget.status === 'draft_ready'
                          ? 'bg-amber-400 text-black hover:bg-amber-300 shadow-[0_0_8px_rgba(245,158,11,0.3)]'
                          : 'bg-[#D2F824] text-black hover:bg-[#bce018] shadow-[0_0_8px_rgba(210,248,36,0.3)]'
                      }`}
                    >
                      {activeTarget.status === 'contacted' ? (
                        <>
                          <Check className="w-3 h-3" />
                          <span>Sent via Gmail</span>
                        </>
                      ) : activeTarget.status === 'draft_ready' ? (
                        <>
                          <Mail className="w-3 h-3" />
                          <span>Review Draft</span>
                        </>
                      ) : (
                        <span>Draft Pitch</span>
                      )}
                    </button>
                    <button 
                      onClick={(e) => handleAuditClick(activeTarget.id, e)}
                      disabled={isAuditing}
                      className="p-1 rounded bg-[#1C212D] text-white hover:text-[#D2F824] border border-[#262D3D] transition-colors disabled:opacity-40"
                      title="Run audit"
                    >
                      <Play className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Bottom Floating Map Utilities HUD */}
            <div className={`absolute bottom-3 ${showInspectorCard ? 'left-[436px]' : 'left-4'} z-10 hidden lg:flex items-center gap-2 text-[11px] font-mono text-[#586274] transition-all duration-300`}>
              <span className="px-2 py-1 rounded bg-[#161A23]/80 border border-[#262D3D] text-[#8B949E]">
                Space + Drag to pan
              </span>
              <span className="px-2 py-1 rounded bg-[#161A23]/80 border border-[#262D3D] text-[#8B949E]">
                Scroll to zoom radius
              </span>
            </div>

            <div className="absolute bottom-3 right-4 z-20 flex items-center gap-2 text-[11px] font-mono text-[#586274]">
              <span className="px-2 py-1 rounded bg-[#161A23]/80 border border-[#262D3D] text-emerald-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> 
                Engine ping: 12ms • Map updates every 3 min
              </span>

              {/* Map Zoom / Layer Tools */}
              <div className="flex items-center bg-[#161A23]/90 border border-[#262D3D] rounded-lg p-0.5">
                <button 
                  onClick={() => setShowInspectorCard(!showInspectorCard)}
                  className="p-1 text-[#8B949E] hover:text-white" 
                  title="Toggle Inspector"
                >
                  <Layers className="w-3.5 h-3.5" />
                </button>
                <button 
                  onClick={() => setRadarZoom((z) => Math.min(z + 0.1, 1.4))}
                  className="p-1 text-[#8B949E] hover:text-white" 
                  title="Zoom In"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
                <button 
                  onClick={() => setRadarZoom((z) => Math.max(z - 0.1, 0.8))}
                  className="p-1 text-[#8B949E] hover:text-white" 
                  title="Zoom Out"
                >
                  <Minus className="w-3.5 h-3.5" />
                </button>
                <button 
                  onClick={() => setRadarZoom(1)}
                  className="p-1 text-[#8B949E] hover:text-white" 
                  title="Reset View"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
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
                        className={`transition-colors cursor-pointer ${
                          isSelected 
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
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${
                            p.opportunityScore >= 80 
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

            {/* Active Inspector Terminal Console Probe Card */}
            {showLogs && (
              <div className="bg-[#161A23] border border-[#262D3D] rounded-xl p-4 shadow-xl">
                <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-[#262D3D]">
                  <div className="flex items-center gap-1.5">
                    <Terminal className="w-4 h-4 text-[#D2F824]" />
                    <span className="text-xs font-bold text-white font-sans uppercase tracking-wider">
                      Diagnostic Inspector Probe
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
                  <p className="text-[#586274]">// Raw HTTP socket inspection</p>
                  <p className="text-rose-400 font-semibold">&gt; GET /contact HTTP/1.1 → 404 Not Found</p>
                  <p className="text-white">Server: nginx/1.18.0 (Ubuntu)</p>
                  <p className="text-white">Content-Type: text/html; charset=UTF-8</p>
                  <p className="text-amber-400">X-Frame-Options: SAMEORIGIN</p>
                  <p className="text-emerald-400">Strict-Transport-Security: max-age=0</p>
                  <p className="text-[#586274]">&gt; Response checksum: 0x9AF83E12</p>
                </div>

                <div className="mt-2.5 flex items-center justify-between text-[11px] font-mono text-[#8B949E]">
                  <span className="truncate max-w-[200px]">
                    Host: {activeTarget?.websiteUrl ? activeTarget.websiteUrl.replace(/https?:\/\//, '') : 'localhost'}
                  </span>
                  <span className="text-[#D2F824] font-bold">Latency: 73ms</span>
                </div>
              </div>
            )}
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
