import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Search, 
  Plus, 
  UploadCloud, 
  Download, 
  Play, 
  Sparkles,
  ChevronRight, 
  Eye,
  BarChart3
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { ImportModal } from '../components/common/ImportModal';
import { NewProspectModal } from '../components/common/NewProspectModal';
import { GenerateDraftModal } from '../components/common/GenerateDraftModal';
import { ProspectDetailModal } from '../components/common/ProspectDetailModal';
import { ProspectScoringModal } from '../components/common/ProspectScoringModal';
import { Prospect, ProspectStatus } from '../types';

export const Prospects: React.FC = () => {
  const { 
    prospects, 
    selectedProspectId, 
    setSelectedProspectId, 
    updateProspectStatus, 
    runAudit, 
    isAuditing, 
    auditingProspectId,
    addToast
  } = useApp();

  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [conditionFilter, setConditionFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isNewProspectModalOpen, setIsNewProspectModalOpen] = useState(false);

  // Phase 5 & 8.2 Modals
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [detailTargetProspect, setDetailTargetProspect] = useState<Prospect | null>(null);
  const [scoringModalProspect, setScoringModalProspect] = useState<Prospect | null>(null);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [generateTargetId, setGenerateTargetId] = useState<string | null>(null);

  const filtered = prospects.filter((p) => {
    const matchesSearch = 
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.category.toLowerCase().includes(search.toLowerCase()) ||
      p.location.city.toLowerCase().includes(search.toLowerCase()) ||
      (p.websiteUrl && p.websiteUrl.toLowerCase().includes(search.toLowerCase()));
    if (!matchesSearch) return false;

    if (statusFilter !== 'all' && p.status !== statusFilter) return false;
    if (conditionFilter !== 'all' && p.websiteStatus !== conditionFilter) return false;

    if (priorityFilter !== 'all') {
      const priority = p.scoring?.priorityLabel || (p.opportunityScore >= 75 ? 'High' : p.opportunityScore >= 45 ? 'Medium' : 'Low');
      if (priorityFilter === 'needs_audit') {
        if (priority !== 'Needs Audit' && p.auditCount > 0) return false;
      } else if (priority.toLowerCase() !== priorityFilter.toLowerCase()) {
        return false;
      }
    }

    return true;
  });

  const handleExportCSV = () => {
    const headers = 'ID,Business Name,Category,City,State,Website URL,Website Status,Score,Status,Last Activity\n';
    const rows = prospects.map((p) => 
      `"${p.id}","${p.name}","${p.category}","${p.location.city}","${p.location.state}","${p.websiteUrl || ''}","${p.websiteStatus}",${p.opportunityScore},"${p.status}","${p.lastActivity}"`
    ).join('\n');

    const blob = new Blob([headers + rows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `leddro_prospects_${new Date().toISOString().substring(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addToast('Exported prospects to CSV', 'success');
  };

  const handleRowClick = (prospect: Prospect) => {
    setSelectedProspectId(prospect.id);
    setDetailTargetProspect(prospect);
    setIsDetailModalOpen(true);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#111214]">
      {/* Header Bar */}
      <div className="px-6 pt-5 pb-3 border-b border-[#22252A] flex flex-col gap-3 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-[24px] font-semibold text-[#F3F4F6] tracking-tight">
              Prospect Management
            </h1>
            <p className="text-[12px] text-[#A0A5AD] mt-0.5">
              Direct pipeline registry of target organizations, audit readiness, and outreach progression.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="md"
              onClick={handleExportCSV}
              leftIcon={<Download className="w-4 h-4" />}
            >
              Export CSV
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
              variant="primary"
              size="md"
              onClick={() => setIsNewProspectModalOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Add Prospect
            </Button>
          </div>
        </div>

        {/* Filters and Search Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-2.5 flex-1 max-w-md">
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-[#727780] absolute left-3 top-2.5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by business name, city, or domain..."
                className="w-full bg-[#17191C] border border-[#2B2F36] rounded pl-9 pr-3 py-1.5 text-[12px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-[#17191C] border border-[#2B2F36] rounded px-2.5 py-1.5 text-[12px] text-[#A0A5AD] focus:border-[#4B5361] outline-none"
            >
              <option value="all">All Priorities</option>
              <option value="high">High Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="low">Low Priority</option>
              <option value="needs_audit">Needs Audit</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#17191C] border border-[#2B2F36] rounded px-2.5 py-1.5 text-[12px] text-[#A0A5AD] focus:border-[#4B5361] outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="new">New</option>
              <option value="needs_audit">Needs Audit</option>
              <option value="needs_review">Needs Review</option>
              <option value="draft_ready">Draft Ready</option>
              <option value="contacted">Contacted</option>
            </select>

            <select
              value={conditionFilter}
              onChange={(e) => setConditionFilter(e.target.value)}
              className="bg-[#17191C] border border-[#2B2F36] rounded px-2.5 py-1.5 text-[12px] text-[#A0A5AD] focus:border-[#4B5361] outline-none"
            >
              <option value="all">All Web Conditions</option>
              <option value="active">Active</option>
              <option value="not_listed">Not listed</option>
              <option value="broken_pages">Broken Pages</option>
              <option value="ssl_expired">SSL Expired</option>
              <option value="dns_error">DNS Error</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="flex-1 overflow-hidden p-6">
        <div className="h-full flex flex-col rounded border border-[#282B31] bg-[#17191C] overflow-hidden">
          <div className="px-4 py-2 border-b border-[#24272D] flex items-center justify-between text-[12px] text-[#A0A5AD] bg-[#1A1C20]">
            <span>Total records: <strong className="text-[#F3F4F6]">{filtered.length}</strong></span>
            <span className="font-mono text-[11px] text-[#727780]">Sync: SQLite Client Persistent</span>
          </div>

          <div className="flex-1 overflow-y-auto">
            <table className="w-full text-left border-collapse text-[12px]">
              <thead className="sticky top-0 bg-[#1A1C20] text-[#727780] font-medium border-b border-[#24272D] z-10">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Business</th>
                  <th className="py-2.5 px-3 font-medium">Category</th>
                  <th className="py-2.5 px-3 font-medium">Location</th>
                  <th className="py-2.5 px-3 font-medium">Website</th>
                  <th className="py-2.5 px-3 font-medium">Opportunity & Priority</th>
                  <th className="py-2.5 px-3 font-medium">Contact Readiness</th>
                  <th className="py-2.5 px-3 font-medium">Audit Freshness</th>
                  <th className="py-2.5 px-3 font-medium">Status Selector</th>
                  <th className="py-2.5 px-3 font-medium">Last Activity</th>
                  <th className="py-2.5 px-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202328] bg-[#17191C]">
                {filtered.map((p) => {
                  const isSelected = selectedProspectId === p.id;
                  const isRowAuditing = isAuditing && auditingProspectId === p.id;
                  const priority = p.scoring?.priorityLabel || (p.opportunityScore >= 75 ? 'High' : p.opportunityScore >= 45 ? 'Medium' : 'Low');
                  const readiness = p.scoring ? p.scoring.contactReadiness : (p.email ? 'unverified' : 'absent');
                  const auditAge = p.scoring?.auditAgeDays;

                  return (
                    <tr
                      key={p.id}
                      onClick={() => handleRowClick(p)}
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
                            <div className="font-medium text-[#F3F4F6] text-[13px]">{p.name}</div>
                            <div className="text-[11px] text-[#727780]">{p.email || p.phone || 'No direct contact'}</div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-3 text-[#A0A5AD]">{p.category}</td>

                      <td className="py-3 px-3 text-[#A0A5AD]">
                        {p.location.city}, {p.location.state}
                      </td>

                      <td className="py-3 px-3">
                        <Badge variant="website" websiteStatus={p.websiteStatus} size="sm" />
                      </td>

                      {/* Opportunity Score & Priority */}
                      <td className="py-3 px-3">
                        <div className="flex flex-col gap-1 items-start">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono text-[12px] font-medium text-[#D8E7A2] bg-[#22271B] px-1.5 py-0.5 rounded border border-[#3E4929]">
                              {p.opportunityScore}/100
                            </span>
                            <span
                              className={`font-mono text-[10px] px-1.5 py-0.2 rounded border uppercase ${
                                priority === 'High'
                                  ? 'bg-[#22271B] text-[#D8E7A2] border-[#3E4929]'
                                  : priority === 'Medium'
                                  ? 'bg-[#232015] text-[#D9B76A] border-[#453D1C]'
                                  : priority === 'Needs Audit'
                                  ? 'bg-[#1D1B2A] text-[#B8A3E0] border-[#393259]'
                                  : 'bg-[#1C1F24] text-[#A0A5AD] border-[#2E3239]'
                              }`}
                            >
                              {priority}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono text-[#727780]">
                              {p.scoring ? `${p.scoring.confidenceScore}% conf` : 'Baseline'}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setScoringModalProspect(p);
                              }}
                              className="text-[10px] text-[#D8E7A2] hover:underline cursor-pointer flex items-center gap-0.5"
                            >
                              <BarChart3 className="w-2.5 h-2.5" />
                              <span>Explain</span>
                            </button>
                          </div>
                        </div>
                      </td>

                      {/* Contact Readiness */}
                      <td className="py-3 px-3">
                        <span
                          className={`font-mono text-[10px] px-1.5 py-0.5 rounded border capitalize ${
                            readiness === 'verified'
                              ? 'bg-[#1A261E] text-[#80B89A] border-[#2D4736]'
                              : readiness === 'unverified'
                              ? 'bg-[#232015] text-[#D9B76A] border-[#453D1C]'
                              : 'bg-[#2B1B1D] text-[#D78383] border-[#522525]'
                          }`}
                        >
                          {readiness}
                        </span>
                      </td>

                      {/* Audit Freshness */}
                      <td className="py-3 px-3 font-mono text-[11px]">
                        {auditAge !== null && auditAge !== undefined ? (
                          auditAge > 30 ? (
                            <span className="text-[#D9B76A]">{auditAge}d ago (stale)</span>
                          ) : (
                            <span className="text-[#80B89A]">{auditAge}d ago</span>
                          )
                        ) : p.latestAuditId ? (
                          <span className="text-[#80B89A]">Audited</span>
                        ) : (
                          <span className="text-[#727780] italic">No audit</span>
                        )}
                      </td>

                      {/* Interactive Status Selector */}
                      <td className="py-3 px-3" onClick={(e) => e.stopPropagation()}>
                        <select
                          value={p.status}
                          onChange={(e) => updateProspectStatus(p.id, e.target.value as ProspectStatus)}
                          className="bg-[#141618] border border-[#2B2F36] rounded px-2 py-1 text-[11px] text-[#F3F4F6] focus:border-[#4B5361] outline-none"
                        >
                          <option value="new">New</option>
                          <option value="needs_audit">Needs audit</option>
                          <option value="needs_review">Needs review</option>
                          <option value="draft_ready">Draft ready</option>
                          <option value="contacted">Contacted</option>
                          <option value="archived">Archived</option>
                        </select>
                      </td>

                      <td className="py-3 px-3 text-[11px] text-[#727780] font-mono">
                        {p.lastActivity}
                      </td>

                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            title="Inspect score breakdown"
                            onClick={() => setScoringModalProspect(p)}
                            className="p-1.5 rounded hover:bg-[#282C33] text-[#A0A5AD] hover:text-[#D8E7A2] transition-colors"
                          >
                            <BarChart3 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            title="Inspect business details"
                            onClick={() => handleRowClick(p)}
                            className="p-1.5 rounded hover:bg-[#282C33] text-[#A0A5AD] hover:text-[#F3F4F6] transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <button
                            title="Run audit crawl"
                            onClick={() => runAudit(p.id)}
                            disabled={isAuditing}
                            className="p-1.5 rounded hover:bg-[#282C33] text-[#A0A5AD] hover:text-[#D8E7A2] transition-colors disabled:opacity-40"
                          >
                            <Play className={`w-3.5 h-3.5 ${isRowAuditing ? 'animate-spin' : ''}`} />
                          </button>
                          <button
                            title="Generate AI email draft"
                            onClick={() => {
                              setSelectedProspectId(p.id);
                              setGenerateTargetId(p.id);
                              setIsGenerateModalOpen(true);
                            }}
                            className="p-1.5 rounded hover:bg-[#282C33] text-[#A0A5AD] hover:text-[#D8E7A2] transition-colors"
                          >
                            <Sparkles className="w-3.5 h-3.5" />
                          </button>
                          <button
                            title="Open audit dossier"
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
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <ImportModal isOpen={isImportModalOpen} onClose={() => setIsImportModalOpen(false)} />
      <NewProspectModal isOpen={isNewProspectModalOpen} onClose={() => setIsNewProspectModalOpen(false)} />
      
      {/* Prospect Detail Inspection Modal */}
      <ProspectDetailModal
        prospect={detailTargetProspect}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onOpenGenerateModal={(id) => {
          setGenerateTargetId(id);
          setIsGenerateModalOpen(true);
        }}
      />

      {/* Explainable Scoring Breakdown Modal */}
      <ProspectScoringModal
        isOpen={Boolean(scoringModalProspect)}
        onClose={() => setScoringModalProspect(null)}
        prospect={scoringModalProspect}
      />

      {/* AI Draft Generation Modal */}
      <GenerateDraftModal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        targetProspectId={generateTargetId}
      />
    </div>
  );
};
