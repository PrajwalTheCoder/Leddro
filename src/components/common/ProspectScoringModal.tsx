import React, { useState } from 'react';
import { X, AlertTriangle, ChevronDown, ChevronRight, CheckCircle2, RefreshCw } from 'lucide-react';
import { Prospect } from '../../types';
import { Button } from './Button';
import { useApp } from '../../context/AppContext';

interface ProspectScoringModalProps {
  isOpen: boolean;
  onClose: () => void;
  prospect: Prospect | null;
}

export const ProspectScoringModal: React.FC<ProspectScoringModalProps> = ({
  isOpen,
  onClose,
  prospect
}) => {
  const { refreshProspects, addToast } = useApp();
  const [expandedFactor, setExpandedFactor] = useState<string | null>(null);
  const [isRecalculating, setIsRecalculating] = useState(false);

  if (!isOpen || !prospect) return null;

  const scoring = prospect.scoring;
  const oppScore = scoring ? scoring.opportunityScore : prospect.opportunityScore;
  const confScore = scoring ? scoring.confidenceScore : 50;
  const priority = scoring ? scoring.priorityLabel : (oppScore >= 75 ? 'High' : oppScore >= 45 ? 'Medium' : 'Low');
  const readiness = scoring ? scoring.contactReadiness : (prospect.email ? 'unverified' : 'absent');
  const auditStatus = scoring ? scoring.auditStatus : (prospect.latestAuditId ? 'completed' : 'none');
  const auditAge = scoring?.auditAgeDays;

  const toggleFactor = (key: string) => {
    setExpandedFactor((prev) => (prev === key ? null : key));
  };

  const handleRecalculate = async () => {
    try {
      setIsRecalculating(true);
      const res = await fetch(`/api/prospects/${prospect.id}/recalculate-score`, { method: 'POST' });
      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }
      await refreshProspects();
      addToast('Opportunity score successfully recalculated against latest audit data.', 'success');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to recalculate score';
      addToast(`Recalculation error: ${msg}`, 'error');
    } finally {
      setIsRecalculating(false);
    }
  };

  const getPriorityBadgeClass = (label: string) => {
    switch (label) {
      case 'High':
        return 'bg-[#22271B] text-[#D8E7A2] border-[#3E4929]';
      case 'Medium':
        return 'bg-[#232015] text-[#D9B76A] border-[#453D1C]';
      case 'Low':
        return 'bg-[#1C1F24] text-[#A0A5AD] border-[#2E3239]';
      case 'Needs Audit':
        return 'bg-[#1D1B2A] text-[#B8A3E0] border-[#393259]';
      default:
        return 'bg-[#1C1F24] text-[#A0A5AD] border-[#2E3239]';
    }
  };

  const getReadinessBadgeClass = (status: string) => {
    switch (status) {
      case 'verified':
        return 'bg-[#1A261E] text-[#80B89A] border-[#2D4736]';
      case 'unverified':
        return 'bg-[#232015] text-[#D9B76A] border-[#453D1C]';
      case 'absent':
        return 'bg-[#2B1B1D] text-[#D78383] border-[#522525]';
      default:
        return 'bg-[#1C1F24] text-[#A0A5AD] border-[#2E3239]';
    }
  };

  const getNatureBadge = (nature?: string) => {
    switch (nature) {
      case 'confirmed_deficiency':
        return (
          <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-[#2B1B1D] text-[#D78383] border border-[#522525]">
            Confirmed Defect
          </span>
        );
      case 'potential_opportunity':
        return (
          <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-[#1C2438] text-[#8DA4EF] border border-[#2D3B5E]">
            Potential Opportunity
          </span>
        );
      case 'failed_diagnostic':
        return (
          <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-[#2B2317] text-[#D9A76A] border border-[#524125]">
            Failed Diagnostic
          </span>
        );
      case 'unknown':
        return (
          <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-[#1C1F24] text-[#8E95A2] border border-[#2B303A]">
            Unknown
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-[#141618] border border-[#2B2F36] rounded shadow-2xl flex flex-col max-h-[90vh] overflow-hidden text-[12px]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#22252A] bg-[#17191C]">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] tracking-wider text-[#727780] uppercase">
              Explainable Scoring Engine
            </span>
            <span className="text-[#3A3F4A]">•</span>
            <span className="font-mono text-[10px] text-[#A0A5AD]">
              Version {scoring?.scoreVersion || '1.0'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRecalculate}
              isLoading={isRecalculating}
              leftIcon={<RefreshCw className="w-3 h-3" />}
            >
              Recalculate
            </Button>
            <button
              onClick={onClose}
              className="text-[#727780] hover:text-[#F3F4F6] p-1 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Business Title & Summary Metrics */}
        <div className="px-5 py-4 border-b border-[#22252A] bg-[#111214]">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div>
              <h2 className="text-[15px] font-medium text-[#F3F4F6]">{prospect.name}</h2>
              <p className="text-[11px] text-[#727780] mt-0.5">
                {prospect.websiteUrl ? (
                  <span className="font-mono">{prospect.websiteUrl}</span>
                ) : (
                  <span className="italic">No website registered</span>
                )}
                {' • '}
                <span>{prospect.category}</span>
                {' • '}
                <span>{prospect.location.city}, {prospect.location.state}</span>
              </p>
            </div>
            <span
              className={`font-mono text-[11px] font-medium px-2 py-0.5 rounded border uppercase ${getPriorityBadgeClass(
                priority
              )}`}
            >
              {priority} Priority
            </span>
          </div>

          {/* Metric Badges Grid */}
          <div className="grid grid-cols-4 gap-2.5">
            <div className="p-2.5 rounded bg-[#17191C] border border-[#23262D]">
              <div className="text-[10px] text-[#727780] uppercase tracking-wider font-mono">
                Opportunity
              </div>
              <div className="text-[18px] font-mono font-medium text-[#D8E7A2] mt-0.5">
                {oppScore}
                <span className="text-[11px] text-[#727780]">/100</span>
              </div>
              <div className="text-[10px] text-[#A0A5AD] mt-0.5">Technical need heuristic</div>
            </div>

            <div className="p-2.5 rounded bg-[#17191C] border border-[#23262D]">
              <div className="text-[10px] text-[#727780] uppercase tracking-wider font-mono">
                Confidence
              </div>
              <div className="text-[18px] font-mono font-medium text-[#F3F4F6] mt-0.5">
                {confScore}
                <span className="text-[11px] text-[#727780]">/100</span>
              </div>
              <div className="text-[10px] text-[#A0A5AD] mt-0.5">Evidence completeness</div>
            </div>

            <div className="p-2.5 rounded bg-[#17191C] border border-[#23262D]">
              <div className="text-[10px] text-[#727780] uppercase tracking-wider font-mono">
                Contact Status
              </div>
              <div className="mt-1">
                <span
                  className={`font-mono text-[10px] px-1.5 py-0.5 rounded border capitalize ${getReadinessBadgeClass(
                    readiness
                  )}`}
                >
                  {readiness}
                </span>
              </div>
              <div className="text-[10px] text-[#A0A5AD] mt-1.5 truncate">
                {prospect.email || prospect.phone || 'No direct channel'}
              </div>
            </div>

            <div className="p-2.5 rounded bg-[#17191C] border border-[#23262D]">
              <div className="text-[10px] text-[#727780] uppercase tracking-wider font-mono">
                Audit Freshness
              </div>
              <div className="text-[12px] font-mono text-[#F3F4F6] mt-1">
                {auditAge !== null && auditAge !== undefined
                  ? `${auditAge}d ago`
                  : auditStatus === 'completed'
                  ? 'Recent'
                  : 'No audit'}
              </div>
              <div className="text-[10px] text-[#A0A5AD] mt-0.5">
                {auditAge !== null && auditAge !== undefined && auditAge > 30 ? 'Stale evidence (>30d)' : 'Status: ' + auditStatus}
              </div>
            </div>
          </div>
        </div>

        {/* Modal Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {/* Factor Breakdown */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium uppercase tracking-wider text-[#727780] font-mono">
                Scoring Factors Breakdown (100 pts total)
              </span>
              <span className="text-[10px] text-[#727780]">Deterministic evidence-based weights</span>
            </div>

            <div className="space-y-1.5">
              {scoring?.factors && scoring.factors.length > 0 ? (
                scoring.factors.map((f) => {
                  const isExpanded = expandedFactor === f.key;
                  const hasEvidence = f.evidence && f.evidence.length > 0;

                  return (
                    <div
                      key={f.key}
                      className="border border-[#23262D] rounded bg-[#17191C] overflow-hidden"
                    >
                      <button
                        onClick={() => toggleFactor(f.key)}
                        className="w-full px-3 py-2.5 flex items-center justify-between text-left hover:bg-[#1D2025] transition-colors"
                      >
                        <div className="flex items-center gap-2 flex-1 pr-3">
                          {hasEvidence ? (
                            isExpanded ? (
                              <ChevronDown className="w-3.5 h-3.5 text-[#A0A5AD] shrink-0" />
                            ) : (
                              <ChevronRight className="w-3.5 h-3.5 text-[#A0A5AD] shrink-0" />
                            )
                          ) : (
                            <span className="w-3.5 h-3.5 inline-block shrink-0" />
                          )}
                          <div className="flex flex-col">
                            <span className="font-medium text-[#F3F4F6] text-[12px]">{f.label}</span>
                            <span className="text-[11px] text-[#727780]">{f.summary}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          {getNatureBadge(f.nature)}
                          <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#131517] text-[#A0A5AD] border border-[#272B33]">
                            {f.status}
                          </span>
                          <div className="text-right min-w-[42px]">
                            <span className="font-mono font-medium text-[12px] text-[#D8E7A2]">
                              +{f.contribution}
                            </span>
                            <span className="font-mono text-[10px] text-[#727780]">
                              /{f.maxContribution}
                            </span>
                          </div>
                        </div>
                      </button>

                      {/* Evidence citations if expanded */}
                      {isExpanded && hasEvidence && (
                        <div className="px-3.5 py-2.5 bg-[#121416] border-t border-[#23262D] space-y-2">
                          <div className="text-[10px] uppercase font-mono tracking-wider text-[#727780]">
                            Documented Audit Evidence ({f.evidence.length} items):
                          </div>
                          <div className="space-y-1.5">
                            {f.evidence.map((ev, idx) => (
                              <div
                                key={idx}
                                className="p-2 rounded bg-[#17191C] border border-[#22252A] flex items-start justify-between gap-2"
                              >
                                <div className="space-y-0.5">
                                  <div className="flex items-center gap-1.5">
                                    <span className="font-medium text-[#F3F4F6] text-[11px]">
                                      {ev.title}
                                    </span>
                                    <span
                                      className={`text-[9px] font-mono px-1 py-0.2 rounded uppercase ${
                                        ev.severity === 'high'
                                          ? 'bg-[#2B1B1D] text-[#D78383] border border-[#522525]'
                                          : ev.severity === 'medium'
                                          ? 'bg-[#232015] text-[#D9B76A] border border-[#453D1C]'
                                          : 'bg-[#17191C] text-[#A0A5AD] border border-[#2B2F36]'
                                      }`}
                                    >
                                      {ev.severity}
                                    </span>
                                  </div>
                                  {ev.observed && (
                                    <p className="text-[11px] text-[#727780] font-mono">{ev.observed}</p>
                                  )}
                                  {ev.findingId && (
                                    <span className="text-[9px] text-[#555B66] font-mono">
                                      Finding ID: {ev.findingId}
                                    </span>
                                  )}
                                </div>
                                <span className="font-mono text-[10px] text-[#D8E7A2] shrink-0">
                                  +{ev.contribution} pts
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div className="p-3 text-[11px] text-[#727780] italic bg-[#17191C] rounded border border-[#23262D]">
                  No breakdown data available. Run an audit or recalculate score.
                </div>
              )}
            </div>
          </div>

          {/* Limitations & Caveats */}
          {scoring?.limitations && scoring.limitations.length > 0 && (
            <div className="p-3 rounded bg-[#17191C] border border-[#2E281F]">
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#D9B76A] mb-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-[#D9B76A]" />
                <span>Known Limitations & Unverified Data</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-[#A0A5AD]">
                {scoring.limitations.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommended Next Actions */}
          {scoring?.recommendedActions && scoring.recommendedActions.length > 0 && (
            <div className="p-3 rounded bg-[#17191C] border border-[#1F2E23]">
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#80B89A] mb-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#80B89A]" />
                <span>Recommended Next Actions</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-[#A0A5AD]">
                {scoring.recommendedActions.map((act, idx) => (
                  <li key={idx}>{act}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Scoring Methodology Note */}
          <div className="text-[10px] text-[#5E6470] border-t border-[#202328] pt-2">
            <strong>Methodology Note:</strong> Leddro opportunity scores are deterministic heuristics
            derived from observed technical audits and discovery metadata. They do not predict conversion
            probabilities or commercial intent.
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-[#22252A] bg-[#17191C] flex justify-end">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
