import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Search, 
  Filter, 
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
  Sparkles
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { ImportModal } from '../components/common/ImportModal';
import { NewProspectModal } from '../components/common/NewProspectModal';
import { GenerateDraftModal } from '../components/common/GenerateDraftModal';
import { ProspectStatus, WebsiteCondition } from '../types';


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
    createEmailDraftForProspect,
    auditReports,
    activeFilter,
    setActiveFilter,
    filterQuery,
    setFilterQuery
  } = useApp();

  const navigate = useNavigate();
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isNewProspectModalOpen, setIsNewProspectModalOpen] = useState(false);
  const [showDetailPanel, setShowDetailPanel] = useState(true);
  const [sortBy, setSortBy] = useState<'score' | 'name' | 'activity'>('score');
  const [sortAsc, setSortAsc] = useState(false);
  const [showVerifiedOnly, setShowVerifiedOnly] = useState(false);
  const [showAlertsOnly, setShowAlertsOnly] = useState(false);

  // Filter prospects
  const filteredProspects = prospects
    .filter((p) => {
      // Search
      const matchesSearch = 
        p.name.toLowerCase().includes(filterQuery.toLowerCase()) ||
        p.category.toLowerCase().includes(filterQuery.toLowerCase()) ||
        p.location.city.toLowerCase().includes(filterQuery.toLowerCase()) ||
        (p.websiteUrl && p.websiteUrl.toLowerCase().includes(filterQuery.toLowerCase()));
      if (!matchesSearch) return false;

      // Status pill filter
      if (activeFilter === 'needs_audit') return p.status === 'needs_audit' || p.auditCount === 0;
      if (activeFilter === 'needs_review') return p.status === 'needs_review';
      if (activeFilter === 'draft_ready') return p.status === 'draft_ready';
      if (activeFilter === 'contacted') return p.status === 'contacted';
      if (activeFilter === 'high_priority') return p.opportunityScore >= 80;

      // Toggles
      if (showVerifiedOnly && p.auditCount === 0) return false;
      if (showAlertsOnly && p.websiteStatus === 'active') return false;

      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'score') {
        return sortAsc ? a.opportunityScore - b.opportunityScore : b.opportunityScore - a.opportunityScore;
      }
      if (sortBy === 'name') {
        return sortAsc ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
      }
      return 0;
    });

  const selectedAudit = selectedProspect?.latestAuditId 
    ? auditReports[selectedProspect.latestAuditId] 
    : undefined;

  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [generateTargetId, setGenerateTargetId] = useState<string | null>(null);

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


  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#111214]">
      {/* Top Header Strip with Title, Filters, and Primary Actions */}
      <div className="px-6 pt-5 pb-3 border-b border-[#22252A] flex flex-col gap-3 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-[24px] font-semibold text-[#F3F4F6] tracking-tight leading-tight">
              Overview
            </h1>
            <p className="text-[12px] text-[#A0A5AD] mt-0.5">
              Your prospect research and technical opportunity matrix at a glance.
            </p>
          </div>

          {/* Primary Action Buttons */}
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate('/discover')}
              leftIcon={<Compass className="w-4 h-4" />}
            >
              Discover prospects
            </Button>
            <Button
              variant="secondary"
              size="md"
              onClick={() => setIsImportModalOpen(true)}
              leftIcon={<UploadCloud className="w-4 h-4" />}
            >
              Import CSV
            </Button>
            <Button
              variant="ghost"
              size="md"
              onClick={() => setIsNewProspectModalOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Add Prospect
            </Button>
          </div>
        </div>

        {/* Filter Pill Row (Matching Haulix UI style: All 10, Active 6, Idle 2, Maintenance 1, etc.) */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-3 py-1 rounded-full text-[12px] font-medium transition-all ${
                activeFilter === 'all'
                  ? 'bg-[#F3F4F6] text-[#111214]'
                  : 'bg-[#17191C] text-[#A0A5AD] hover:text-[#F3F4F6] border border-[#2B2F36]'
              }`}
            >
              All <span className="ml-1 opacity-75">{prospects.length}</span>
            </button>
            <button
              onClick={() => setActiveFilter('needs_review')}
              className={`px-3 py-1 rounded-full text-[12px] font-medium transition-all ${
                activeFilter === 'needs_review'
                  ? 'bg-[#F3F4F6] text-[#111214]'
                  : 'bg-[#17191C] text-[#A0A5AD] hover:text-[#F3F4F6] border border-[#2B2F36]'
              }`}
            >
              Needs review <span className="ml-1 opacity-75">{prospects.filter((p) => p.status === 'needs_review').length}</span>
            </button>
            <button
              onClick={() => setActiveFilter('draft_ready')}
              className={`px-3 py-1 rounded-full text-[12px] font-medium transition-all ${
                activeFilter === 'draft_ready'
                  ? 'bg-[#F3F4F6] text-[#111214]'
                  : 'bg-[#17191C] text-[#A0A5AD] hover:text-[#F3F4F6] border border-[#2B2F36]'
              }`}
            >
              Draft ready <span className="ml-1 opacity-75">{prospects.filter((p) => p.status === 'draft_ready').length}</span>
            </button>
            <button
              onClick={() => setActiveFilter('needs_audit')}
              className={`px-3 py-1 rounded-full text-[12px] font-medium transition-all ${
                activeFilter === 'needs_audit'
                  ? 'bg-[#F3F4F6] text-[#111214]'
                  : 'bg-[#17191C] text-[#A0A5AD] hover:text-[#F3F4F6] border border-[#2B2F36]'
              }`}
            >
              Needs audit <span className="ml-1 opacity-75">{prospects.filter((p) => p.auditCount === 0).length}</span>
            </button>
            <button
              onClick={() => setActiveFilter('high_priority')}
              className={`px-3 py-1 rounded-full text-[12px] font-medium transition-all ${
                activeFilter === 'high_priority'
                  ? 'bg-[#F3F4F6] text-[#111214]'
                  : 'bg-[#17191C] text-[#A0A5AD] hover:text-[#F3F4F6] border border-[#2B2F36]'
              }`}
            >
              Score ≥ 80 <span className="ml-1 opacity-75">{prospects.filter((p) => p.opportunityScore >= 80).length}</span>
            </button>
          </div>

          {/* Right Switches (Like Haulix: Show routes / Show alerts) */}
          <div className="flex items-center gap-4 text-[12px] text-[#A0A5AD]">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <span>Show audited only</span>
              <button
                type="button"
                role="switch"
                aria-checked={showVerifiedOnly}
                onClick={() => setShowVerifiedOnly(!showVerifiedOnly)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out ${
                  showVerifiedOnly ? 'bg-[#80B89A]' : 'bg-[#2A2E35]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-[#111214] shadow ring-0 transition duration-200 ease-in-out ${
                    showVerifiedOnly ? 'translate-x-4' : 'translate-x-0'
                  }`}
                />
              </button>
            </label>

            <label className="flex items-center gap-2 cursor-pointer select-none">
              <span>Issues only</span>
              <button
                type="button"
                role="switch"
                aria-checked={showAlertsOnly}
                onClick={() => setShowAlertsOnly(!showAlertsOnly)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out ${
                  showAlertsOnly ? 'bg-[#D8E7A2]' : 'bg-[#2A2E35]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-[#111214] shadow ring-0 transition duration-200 ease-in-out ${
                    showAlertsOnly ? 'translate-x-4' : 'translate-x-0'
                  }`}
                />
              </button>
            </label>
          </div>
        </div>
      </div>

      {/* Main Workspace Area: Table + Detail Inspector (Matches Haulix Layout) */}
      <div className="flex-1 flex overflow-hidden p-6 gap-6 relative">
        {/* Central Prospects Matrix / Table */}
        <div className="flex-1 flex flex-col rounded border border-[#282B31] bg-[#17191C] overflow-hidden">
          {/* Table Header Bar */}
          <div className="px-4 py-2.5 border-b border-[#24272D] flex items-center justify-between bg-[#1D2024]/50">
            <div className="flex items-center gap-2 text-[12px] text-[#A0A5AD]">
              <span>Showing <strong>{filteredProspects.length}</strong> prospects</span>
              {activeFilter !== 'all' && (
                <span className="text-[11px] text-[#727780]">filtered by {activeFilter.replace('_', ' ')}</span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (sortBy === 'score') setSortAsc(!sortAsc);
                  else {
                    setSortBy('score');
                    setSortAsc(false);
                  }
                }}
                className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium text-[#A0A5AD] hover:text-[#F3F4F6] hover:bg-[#24272C] transition-colors"
              >
                <ArrowUpDown className="w-3 h-3" />
                Score {sortBy === 'score' ? (sortAsc ? '↑' : '↓') : ''}
              </button>
            </div>
          </div>

          {/* Table Container */}
          <div className="flex-1 overflow-y-auto">
            <table className="w-full text-left border-collapse text-[12px]">
              <thead className="sticky top-0 bg-[#1A1C20] text-[#727780] font-medium border-b border-[#24272D] z-10">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Business</th>
                  <th className="py-2.5 px-3 font-medium">Category</th>
                  <th className="py-2.5 px-3 font-medium">Website Status</th>
                  <th className="py-2.5 px-3 font-medium">Score</th>
                  <th className="py-2.5 px-3 font-medium">Status</th>
                  <th className="py-2.5 px-3 font-medium">Last Activity</th>
                  <th className="py-2.5 px-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202328] bg-[#17191C]">
                {filteredProspects.map((p) => {
                  const isSelected = selectedProspectId === p.id;
                  const isRowAuditing = isAuditing && auditingProspectId === p.id;

                  return (
                    <tr
                      key={p.id}
                      onClick={() => {
                        setSelectedProspectId(p.id);
                        setShowDetailPanel(true);
                      }}
                      className={`cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-[#22262C] border-l-2 border-l-[#D8E7A2]'
                          : 'hover:bg-[#1C1F24]'
                      }`}
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded bg-[#1D2024] border border-[#2E3239] flex items-center justify-center shrink-0">
                            <Building2 className="w-3.5 h-3.5 text-[#A0A5AD]" />
                          </div>
                          <div>
                            <div className="font-medium text-[#F3F4F6] text-[13px] flex items-center gap-1.5">
                              {p.name}
                              {p.tags.includes('High Value') && (
                                <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-[#2A2518] text-[#D8B16C] border border-[#44381F]">
                                  VIP
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-[#727780] font-mono truncate max-w-xs">
                              {p.websiteUrl ? p.websiteUrl.replace(/https?:\/\//, '') : 'No website registered'}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-3 text-[#A0A5AD]">
                        <div>{p.category}</div>
                        <div className="text-[11px] text-[#727780]">{p.location.city}, {p.location.state}</div>
                      </td>

                      <td className="py-3 px-3">
                        <Badge variant="website" websiteStatus={p.websiteStatus} size="sm" />
                      </td>

                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <span className={`font-mono font-medium text-[12px] px-1.5 py-0.5 rounded border ${
                            p.opportunityScore >= 80 
                              ? 'bg-[#242A1B] text-[#D8E7A2] border-[#3E4929]'
                              : p.opportunityScore >= 65
                              ? 'bg-[#262419] text-[#D8B16C] border-[#443B21]'
                              : 'bg-[#1F2228] text-[#A0A5AD] border-[#2E333C]'
                          }`}>
                            {p.opportunityScore}/100
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-3">
                        <Badge variant="status" prospectStatus={p.status} size="sm" />
                      </td>

                      <td className="py-3 px-3 text-[11px] text-[#727780] font-mono">
                        {p.lastActivity}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                          <button
                            title="Run website diagnostic audit"
                            onClick={(e) => handleAuditClick(p.id, e)}
                            disabled={isAuditing}
                            className="p-1.5 rounded hover:bg-[#282C33] text-[#A0A5AD] hover:text-[#D8E7A2] transition-colors disabled:opacity-40"
                          >
                            <Play className={`w-3.5 h-3.5 ${isRowAuditing ? 'animate-spin' : ''}`} />
                          </button>
                          <button
                            title="Generate AI email draft"
                            onClick={(e) => handleCreateDraftClick(p.id, e)}
                            className="p-1.5 rounded hover:bg-[#282C33] text-[#A0A5AD] hover:text-[#D8E7A2] transition-colors"
                          >
                            <Sparkles className="w-3.5 h-3.5" />
                          </button>

                          <button
                            title="View full audit dossier"
                            onClick={() => {
                              setSelectedProspectId(p.id);
                              navigate('/audits');
                            }}
                            className="p-1.5 rounded hover:bg-[#282C33] text-[#A0A5AD] hover:text-[#F3F4F6] transition-colors"
                          >
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}

                {filteredProspects.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-[#727780]">
                      <div className="flex flex-col items-center gap-2">
                        <Building2 className="w-8 h-8 text-[#30343A]" />
                        <div className="text-[13px] text-[#A0A5AD]">No prospects match the selected filter.</div>
                        <Button variant="secondary" size="sm" onClick={() => { setActiveFilter('all'); setFilterQuery(''); }}>
                          Reset Filters
                        </Button>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Audit progress banner if auditing */}
          {isAuditing && (
            <div className="px-4 py-2 bg-[#20251B] border-t border-[#374225] flex items-center justify-between text-[12px] text-[#D8E7A2] shrink-0 animate-in fade-in">
              <div className="flex items-center gap-2 font-mono">
                <span className="w-2 h-2 rounded-full bg-[#D8E7A2] animate-ping" />
                <span>Engine: {auditProgressMessage}</span>
              </div>
              <span className="text-[11px] text-[#A0A5AD]">Simulated headless crawler</span>
            </div>
          )}
        </div>

        {/* Right-Side Detail Panel (Styled after the Haulix overlay inspector card) */}
        {selectedProspect && showDetailPanel && (
          <div className="w-88 lg:w-96 shrink-0 rounded border border-[#30343A] bg-[#17191C] shadow-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-right-2">
            {/* Inspector Top Bar */}
            <div className="px-4 py-3 bg-[#1D2024] border-b border-[#2B2F36] flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-6 h-6 rounded bg-[#24272C] border border-[#363B44] flex items-center justify-center shrink-0">
                  <Building2 className="w-3.5 h-3.5 text-[#D8E7A2]" />
                </div>
                <div className="truncate">
                  <div className="text-[13px] font-semibold text-[#F3F4F6] truncate leading-tight">
                    {selectedProspect.name}
                  </div>
                  <div className="text-[11px] text-[#727780] truncate leading-none mt-0.5">
                    {selectedProspect.category} · {selectedProspect.location.city}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <Badge variant="status" prospectStatus={selectedProspect.status} size="sm" />
                <button
                  onClick={() => setShowDetailPanel(false)}
                  className="p-1 rounded text-[#727780] hover:text-[#F3F4F6] hover:bg-[#25282F]"
                  title="Close Inspector"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Inspector Content (Scrollable) */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
              {/* Opportunity Score Block */}
              <div className="rounded p-3 bg-[#111214] border border-[#24272D] flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-[12px] font-medium text-[#A0A5AD]">Opportunity Score</span>
                  <span className="text-[14px] font-mono font-semibold text-[#D8E7A2]">
                    {selectedProspect.opportunityScore}/100
                  </span>
                </div>
                {/* Restrained horizontal meter instead of truck speedometer */}
                <div className="w-full bg-[#1D2024] h-2 rounded-full overflow-hidden border border-[#292D34]">
                  <div
                    className="h-full bg-[#D8E7A2] transition-all duration-500 rounded-full"
                    style={{ width: `${selectedProspect.opportunityScore}%` }}
                  />
                </div>
                <div className="grid grid-cols-3 gap-2 pt-1 text-[11px] font-mono text-[#727780]">
                  <div>Urgency: <strong className="text-[#A0A5AD]">{selectedProspect.scoreBreakdown.technicalUrgency}</strong></div>
                  <div>Intent: <strong className="text-[#A0A5AD]">{selectedProspect.scoreBreakdown.commercialIntent}</strong></div>
                  <div>Ease: <strong className="text-[#A0A5AD]">{selectedProspect.scoreBreakdown.resolutionEase}</strong></div>
                </div>
              </div>

              {/* Website Status & Reachability */}
              <div className="rounded p-3 bg-[#1D2024] border border-[#2A2E35] flex flex-col gap-2">
                <div className="text-[11px] font-medium text-[#727780] uppercase tracking-wider">
                  Target Domain Infrastructure
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[#A0A5AD]">Domain status:</span>
                  <Badge variant="website" websiteStatus={selectedProspect.websiteStatus} size="sm" />
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[#A0A5AD]">URL:</span>
                  {selectedProspect.websiteUrl ? (
                    <a
                      href={selectedProspect.websiteUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-[11px] text-[#91B7D8] hover:underline flex items-center gap-1"
                    >
                      {selectedProspect.websiteUrl.replace(/https?:\/\//, '')}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-[11px] text-[#727780] italic">Unregistered in DNS</span>
                  )}
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[#A0A5AD]">Audits executed:</span>
                  <span className="font-mono text-[#F3F4F6]">{selectedProspect.auditCount} run</span>
                </div>
              </div>

              {/* Primary Recommended Action Card */}
              <div className="rounded p-3 bg-[#201F18] border border-[#3C3622] flex flex-col gap-1.5">
                <div className="flex items-center gap-1.5 text-[12px] font-medium text-[#D8B16C]">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  <span>Recommended Action</span>
                </div>
                <p className="text-[12px] text-[#F3F4F6] leading-relaxed">
                  {selectedProspect.recommendedAction}
                </p>
              </div>

              {/* Latest Findings Summary */}
              {selectedAudit ? (
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between text-[12px]">
                    <span className="font-medium text-[#A0A5AD]">Findings ({selectedAudit.findings.length})</span>
                    <span className="text-[11px] font-mono text-[#727780]">{selectedAudit.timestamp}</span>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    {selectedAudit.findings.map((f) => (
                      <div
                        key={f.id}
                        className="p-2.5 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1 text-[12px]"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-[#F3F4F6] truncate">{f.title}</span>
                          <Badge variant="severity" severity={f.severity} size="sm" />
                        </div>
                        <p className="text-[11px] text-[#727780] line-clamp-2">{f.observed}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded bg-[#111214] border border-[#24272D] text-center text-[12px] text-[#727780]">
                  No audit report generated yet for this record.
                </div>
              )}
            </div>

            {/* Direct Actions (Pinned at bottom) */}
            <div className="p-4 border-t border-[#262A30] bg-[#17191C] shrink-0 flex flex-col gap-2">
              <Button
                variant="primary"
                size="md"
                onClick={() => handleAuditClick(selectedProspect.id)}
                isLoading={isAuditing && auditingProspectId === selectedProspect.id}
                leftIcon={<Play className="w-3.5 h-3.5" />}
                className="w-full"
              >
                {selectedProspect.auditCount > 0 ? 'Re-run Website Audit' : 'Run Website Audit'}
              </Button>

              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="secondary"
                  size="md"
                  onClick={() => handleCreateDraftClick(selectedProspect.id)}
                  leftIcon={<Mail className="w-3.5 h-3.5" />}
                >
                  Create Draft
                </Button>
                <Button
                  variant="secondary"
                  size="md"
                  onClick={() => {
                    setSelectedProspectId(selectedProspect.id);
                    navigate('/audits');
                  }}
                  leftIcon={<FileText className="w-3.5 h-3.5" />}
                >
                  View Dossier
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Bar: Operational shortcuts & status (Like Haulix bottom hint bar) */}
      <div className="px-6 py-2.5 bg-[#111214] border-t border-[#22252A] flex items-center justify-between text-[11px] text-[#727780] shrink-0 font-mono">
        <div className="flex items-center gap-4">
          <span>Use <strong>↑ / ↓</strong> to browse rows</span>
          <span className="text-[#30343A]">|</span>
          <span><strong>Esc</strong> to close inspector</span>
          <span className="text-[#30343A]">|</span>
          <span>Press <strong>⌘K</strong> for global command console</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#80B89A]" />
          <span>Local SQLite cache synchronized</span>
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

