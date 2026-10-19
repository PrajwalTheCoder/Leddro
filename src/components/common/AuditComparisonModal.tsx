import React, { useState, useEffect } from 'react';
import { 
  X, 
  ArrowLeftRight, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  RefreshCw, 
  ChevronRight, 
  Layers, 
  ArrowUpRight, 
  ArrowDownRight, 
  Minus, 
  AlertTriangle 
} from 'lucide-react';
import { Button } from './Button';
import { Badge } from './Badge';
import { useApp } from '../../context/AppContext';
import { 
  AuditReport, 
  AuditComparisonResponse, 
  FindingComparisonItem 
} from '../../types';

interface AuditComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialProspectId?: string;
  initialOlderAuditId?: string;
  initialNewerAuditId?: string;
}

export const AuditComparisonModal: React.FC<AuditComparisonModalProps> = ({
  isOpen,
  onClose,
  initialProspectId,
  initialOlderAuditId,
  initialNewerAuditId,
}) => {
  const { 
    prospects, 
    selectedProspectId, 
    compareAudits, 
    fetchProspectAudits, 
    addToast 
  } = useApp();

  const [targetProspectId, setTargetProspectId] = useState<string>(
    initialProspectId || selectedProspectId || (prospects[0]?.id || '')
  );

  const [prospectAudits, setProspectAudits] = useState<AuditReport[]>([]);
  const [isLoadingAudits, setIsLoadingAudits] = useState(false);

  const [olderAuditId, setOlderAuditId] = useState<string>(initialOlderAuditId || '');
  const [newerAuditId, setNewerAuditId] = useState<string>(initialNewerAuditId || '');

  const [isComparing, setIsComparing] = useState(false);
  const [comparison, setComparison] = useState<AuditComparisonResponse | null>(null);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'all' | 'resolved' | 'new' | 'persistent' | 'inconclusive' | 'measurements'>('all');

  const currentProspect = prospects.find((p) => p.id === targetProspectId) || prospects[0];

  const isMountedRef = React.useRef(true);
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Fetch all stored audits for the selected prospect
  useEffect(() => {
    if (!isOpen || !targetProspectId) return;

    setIsLoadingAudits(true);
    setComparison(null);
    setComparisonError(null);

    fetchProspectAudits(targetProspectId)
      .then((audits) => {
        if (!isMountedRef.current) return;
        // Sort chronologically ascending (oldest first, newest last)
        const sorted = [...audits].sort((a, b) => {
          const tA = new Date(a.timestamp).getTime() || 0;
          const tB = new Date(b.timestamp).getTime() || 0;
          return tA - tB;
        });
        setProspectAudits(sorted);

        // Auto-select sensible defaults if at least 2 audits exist
        if (sorted.length >= 2) {
          const oldId = initialOlderAuditId && sorted.some(a => a.id === initialOlderAuditId) 
            ? initialOlderAuditId 
            : sorted[0].id;
          const newId = initialNewerAuditId && sorted.some(a => a.id === initialNewerAuditId)
            ? initialNewerAuditId
            : sorted[sorted.length - 1].id;

          setOlderAuditId(oldId);
          setNewerAuditId(newId);
        } else if (sorted.length === 1) {
          setOlderAuditId(sorted[0].id);
          setNewerAuditId('');
        } else {
          setOlderAuditId('');
          setNewerAuditId('');
        }
      })
      .catch((err) => {
        if (!isMountedRef.current) return;
        setComparisonError(err.message || 'Failed to retrieve prospect audit history.');
      })
      .finally(() => {
        if (isMountedRef.current) setIsLoadingAudits(false);
      });
  }, [isOpen, targetProspectId]);

  // Execute comparison when both IDs are chosen
  const handleExecuteComparison = async () => {
    if (isComparing) return;

    if (!olderAuditId || !newerAuditId) {
      addToast('Please select both an older and newer audit to compare.', 'warning');
      return;
    }

    if (olderAuditId === newerAuditId) {
      setComparisonError('Cannot compare an audit with itself. Please select two distinct audits.');
      return;
    }

    setIsComparing(true);
    setComparisonError(null);

    try {
      const result = await compareAudits(olderAuditId, newerAuditId);
      if (!isMountedRef.current) return;
      setComparison(result);
      setActiveTab('all');
    } catch (err: any) {
      if (!isMountedRef.current) return;
      setComparisonError(err.message || 'Comparison failed.');
      setComparison(null);
    } finally {
      if (isMountedRef.current) {
        setIsComparing(false);
      }
    }
  };

  // Auto-run comparison once IDs are set and verified
  useEffect(() => {
    if (olderAuditId && newerAuditId && olderAuditId !== newerAuditId && prospectAudits.length >= 2) {
      handleExecuteComparison();
    }
  }, [olderAuditId, newerAuditId]);

  // Keyboard Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-3 sm:p-6 overflow-hidden">
      <div className="w-full max-w-5xl rounded-lg border border-[#30343A] bg-[#141618] shadow-2xl flex flex-col h-[92vh] max-h-[900px] overflow-hidden text-[#F3F4F6]">
        
        {/* Top Header */}
        <div className="px-6 py-4 border-b border-[#24272D] flex items-center justify-between bg-[#17191C] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-[#1D2024] border border-[#30343A] flex items-center justify-center text-[#D8E7A2]">
              <ArrowLeftRight className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-[16px] font-semibold tracking-tight text-[#F3F4F6]">
                  Website Audit Comparison &amp; Change Detection
                </h2>
                <span className="text-[10px] font-mono uppercase bg-[#22271B] text-[#D8E7A2] border border-[#3E4929] px-2 py-0.5 rounded">
                  Deterministic v1.0
                </span>
              </div>
              <p className="text-[12px] text-[#A0A5AD] mt-0.5">
                Evidence-based before/after analysis for verified improvements, regressions, and inconclusive checks.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded text-[#727780] hover:text-[#F3F4F6] hover:bg-[#202328] transition-colors"
            title="Close modal"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Audit Selection Bar */}
        <div className="px-6 py-3.5 bg-[#17191C] border-b border-[#24272D] flex flex-wrap items-center justify-between gap-4 shrink-0 text-[12px]">
          {/* Target Prospect Selector */}
          <div className="flex items-center gap-2.5">
            <span className="text-[#727780] font-medium">Prospect:</span>
            <select
              value={targetProspectId}
              onChange={(e) => setTargetProspectId(e.target.value)}
              aria-label="Select prospect to compare audits"
              className="bg-[#121416] border border-[#2B2F36] rounded px-3 py-1.5 text-[#F3F4F6] focus:border-[#4B5361] outline-none text-[12px]"
            >
              {prospects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.websiteUrl || 'No domain'})
                </option>
              ))}
            </select>
          </div>

          {/* Audit Pair Selectors */}
          {prospectAudits.length >= 2 ? (
            <div className="flex flex-wrap items-center gap-3">
              {/* Older Audit */}
              <div className="flex items-center gap-2">
                <span className="text-[#A0A5AD]">Before (Older):</span>
                <select
                  value={olderAuditId}
                  onChange={(e) => setOlderAuditId(e.target.value)}
                  aria-label="Select older audit for before baseline"
                  className="bg-[#121416] border border-[#2B2F36] rounded px-2.5 py-1.5 text-[11px] font-mono text-[#F3F4F6] focus:border-[#4B5361] outline-none"
                >
                  {prospectAudits.map((a) => (
                    <option key={a.id} value={a.id} disabled={a.id === newerAuditId}>
                      {a.timestamp} · Score: {a.overallScore}/100 {a.status === 'failed' ? '(FAILED)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <ChevronRight className="w-4 h-4 text-[#4E5460]" />

              {/* Newer Audit */}
              <div className="flex items-center gap-2">
                <span className="text-[#A0A5AD]">After (Newer):</span>
                <select
                  value={newerAuditId}
                  onChange={(e) => setNewerAuditId(e.target.value)}
                  aria-label="Select newer audit for after comparison"
                  className="bg-[#121416] border border-[#2B2F36] rounded px-2.5 py-1.5 text-[11px] font-mono text-[#F3F4F6] focus:border-[#4B5361] outline-none"
                >
                  {prospectAudits.map((a) => (
                    <option key={a.id} value={a.id} disabled={a.id === olderAuditId}>
                      {a.timestamp} · Score: {a.overallScore}/100 {a.status === 'failed' ? '(FAILED)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                variant="secondary"
                size="sm"
                onClick={handleExecuteComparison}
                isLoading={isComparing}
                leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isComparing ? 'animate-spin' : ''}`} />}
              >
                Re-compare
              </Button>
            </div>
          ) : (
            <div className="text-[12px] text-[#A0A5AD] font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-[#E5A96A]" />
              <span>Available audits: {prospectAudits.length} (at least 2 required)</span>
            </div>
          )}
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">

          {/* Insufficient Audits Empty State */}
          {!isLoadingAudits && prospectAudits.length < 2 && (
            <div className="my-auto py-12 px-6 rounded-lg border border-[#262A30] bg-[#17191C] text-center max-w-lg mx-auto flex flex-col items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-[#1F2226] border border-[#2F3540] flex items-center justify-center text-[#E5A96A]">
                <Layers className="w-6 h-6" />
              </div>
              <div className="flex flex-col gap-1.5">
                <h3 className="text-[16px] font-semibold text-[#F3F4F6]">
                  {prospectAudits.length === 0 ? 'No Audit History Available' : 'Second Audit Required'}
                </h3>
                <p className="text-[12px] text-[#A0A5AD] leading-relaxed">
                  {prospectAudits.length === 0
                    ? `No diagnostic audits have been executed yet for ${currentProspect?.name || 'this website'}. Execute an initial audit to establish a baseline.`
                    : `Leddro has recorded 1 audit (${prospectAudits[0].timestamp}). At least two audits of the same domain are required to evaluate resolved, new, and persistent issues.`}
                </p>
              </div>
              <div className="p-3 bg-[#121416] rounded border border-[#25282F] text-[11px] text-[#727780] text-left w-full font-mono">
                <strong className="text-[#A0A5AD]">Rule:</strong> A missing finding in a newer audit does not automatically mean an issue is fixed. Leddro requires explicit positive proof of a passing check to classify any issue as resolved.
              </div>
            </div>
          )}

          {/* Error Banner */}
          {comparisonError && (
            <div className="p-4 rounded border border-[#522525] bg-[#241414] text-[#E58080] flex items-start gap-3 text-[12px]">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="flex flex-col gap-1">
                <span className="font-semibold">Comparison Blocked</span>
                <span>{comparisonError}</span>
              </div>
            </div>
          )}

          {/* Loading Indicator */}
          {(isLoadingAudits || isComparing) && !comparison && (
            <div className="my-auto py-16 flex flex-col items-center justify-center gap-3 text-[#A0A5AD]">
              <RefreshCw className="w-6 h-6 animate-spin text-[#D8E7A2]" />
              <span className="text-[12px] font-mono">Evaluating stored audit evidence &amp; telemetry...</span>
            </div>
          )}

          {/* Comparison Results */}
          {comparison && !isComparing && (
            <>
              {/* Reliability & Execution Status Banner */}
              <div className={`p-4 rounded-lg border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-[12px] ${
                comparison.isReliable 
                  ? 'border-[#2D3A24] bg-[#192016]' 
                  : 'border-[#463920] bg-[#221C12]'
              }`}>
                <div className="flex items-center gap-3">
                  {comparison.isReliable ? (
                    <div className="w-7 h-7 rounded bg-[#25321E] border border-[#3E4E30] flex items-center justify-center text-[#D8E7A2]">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                  ) : (
                    <div className="w-7 h-7 rounded bg-[#362A17] border border-[#554222] flex items-center justify-center text-[#E5A96A]">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <strong className={`font-semibold ${comparison.isReliable ? 'text-[#D8E7A2]' : 'text-[#E5A96A]'}`}>
                        {comparison.isReliable ? 'Complete & Reliable Audit Comparison' : 'Partial Audit Comparison (Caveats Apply)'}
                      </strong>
                      <span className="font-mono text-[10px] text-[#A0A5AD] bg-[#121416] px-1.5 py-0.5 rounded border border-[#25282F]">
                        {comparison.executionStatus.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#A0A5AD] mt-0.5">
                      Comparing {comparison.olderAuditId} ({comparison.olderTimestamp}) with {comparison.newerAuditId} ({comparison.newerTimestamp}) on {comparison.url}
                    </p>
                  </div>
                </div>

                <div className="font-mono text-[11px] text-[#A0A5AD] bg-[#121416] px-2.5 py-1 rounded border border-[#25282F] shrink-0">
                  {comparison.summary.comparableMeasurementsCount} telemetry metrics compared
                </div>
              </div>

              {/* Limitations & Caveats if any */}
              {comparison.limitations && comparison.limitations.length > 0 && (
                <div className="p-3 bg-[#1A1813] border border-[#3A3222] rounded text-[11px] text-[#C9A96E] flex flex-col gap-1">
                  <div className="font-semibold flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-[#E5A96A]" />
                    <span>Evidence Limitations:</span>
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 pl-1 text-[11px] text-[#AFA38E]">
                    {comparison.limitations.map((lim, idx) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Summary Counts Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* Resolved */}
                <div 
                  onClick={() => setActiveTab('resolved')}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    activeTab === 'resolved' 
                      ? 'bg-[#1C261B] border-[#435936] ring-1 ring-[#D8E7A2]' 
                      : 'bg-[#17191C] border-[#2B2F36] hover:border-[#3E4550]'
                  }`}
                >
                  <div className="flex items-center justify-between text-[#88B87A]">
                    <span className="text-[11px] font-medium uppercase tracking-wider">Resolved</span>
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div className="text-[24px] font-bold text-[#D8E7A2] font-mono mt-1">
                    {comparison.summary.resolvedCount}
                  </div>
                  <p className="text-[10px] text-[#7A8574] mt-0.5">Issues confirmed fixed</p>
                </div>

                {/* New */}
                <div 
                  onClick={() => setActiveTab('new')}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    activeTab === 'new' 
                      ? 'bg-[#291B1C] border-[#663A3C] ring-1 ring-[#E58080]' 
                      : 'bg-[#17191C] border-[#2B2F36] hover:border-[#3E4550]'
                  }`}
                >
                  <div className="flex items-center justify-between text-[#E58080]">
                    <span className="text-[11px] font-medium uppercase tracking-wider">Newly Detected</span>
                    <AlertCircle className="w-4 h-4" />
                  </div>
                  <div className="text-[24px] font-bold text-[#F3A5A5] font-mono mt-1">
                    {comparison.summary.newCount}
                  </div>
                  <p className="text-[10px] text-[#857474] mt-0.5">Newly confirmed issues</p>
                </div>

                {/* Persistent */}
                <div 
                  onClick={() => setActiveTab('persistent')}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    activeTab === 'persistent' 
                      ? 'bg-[#202328] border-[#434B57] ring-1 ring-[#A0A5AD]' 
                      : 'bg-[#17191C] border-[#2B2F36] hover:border-[#3E4550]'
                  }`}
                >
                  <div className="flex items-center justify-between text-[#A0A5AD]">
                    <span className="text-[11px] font-medium uppercase tracking-wider">Persistent</span>
                    <Layers className="w-4 h-4" />
                  </div>
                  <div className="text-[24px] font-bold text-[#F3F4F6] font-mono mt-1">
                    {comparison.summary.persistentCount}
                  </div>
                  <p className="text-[10px] text-[#727780] mt-0.5">Present in both audits</p>
                </div>

                {/* Inconclusive */}
                <div 
                  onClick={() => setActiveTab('inconclusive')}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    activeTab === 'inconclusive' 
                      ? 'bg-[#272118] border-[#5E4E30] ring-1 ring-[#E5A96A]' 
                      : 'bg-[#17191C] border-[#2B2F36] hover:border-[#3E4550]'
                  }`}
                >
                  <div className="flex items-center justify-between text-[#E5A96A]">
                    <span className="text-[11px] font-medium uppercase tracking-wider">Inconclusive</span>
                    <HelpCircle className="w-4 h-4" />
                  </div>
                  <div className="text-[24px] font-bold text-[#F5C796] font-mono mt-1">
                    {comparison.summary.inconclusiveCount}
                  </div>
                  <p className="text-[10px] text-[#807565] mt-0.5">Missing or incomplete evidence</p>
                </div>
              </div>

              {/* View Tabs */}
              <div className="flex items-center gap-1 border-b border-[#24272D] text-[12px] font-medium pt-2">
                <button
                  onClick={() => setActiveTab('all')}
                  className={`px-3 py-2 border-b-2 transition-colors ${
                    activeTab === 'all'
                      ? 'border-[#D8E7A2] text-[#D8E7A2]'
                      : 'border-transparent text-[#727780] hover:text-[#F3F4F6]'
                  }`}
                >
                  All Findings ({comparison.summary.totalFindingsEvaluated})
                </button>
                <button
                  onClick={() => setActiveTab('resolved')}
                  className={`px-3 py-2 border-b-2 transition-colors ${
                    activeTab === 'resolved'
                      ? 'border-[#88B87A] text-[#88B87A]'
                      : 'border-transparent text-[#727780] hover:text-[#F3F4F6]'
                  }`}
                >
                  Resolved ({comparison.summary.resolvedCount})
                </button>
                <button
                  onClick={() => setActiveTab('new')}
                  className={`px-3 py-2 border-b-2 transition-colors ${
                    activeTab === 'new'
                      ? 'border-[#E58080] text-[#E58080]'
                      : 'border-transparent text-[#727780] hover:text-[#F3F4F6]'
                  }`}
                >
                  New ({comparison.summary.newCount})
                </button>
                <button
                  onClick={() => setActiveTab('persistent')}
                  className={`px-3 py-2 border-b-2 transition-colors ${
                    activeTab === 'persistent'
                      ? 'border-[#A0A5AD] text-[#F3F4F6]'
                      : 'border-transparent text-[#727780] hover:text-[#F3F4F6]'
                  }`}
                >
                  Persistent ({comparison.summary.persistentCount})
                </button>
                <button
                  onClick={() => setActiveTab('inconclusive')}
                  className={`px-3 py-2 border-b-2 transition-colors ${
                    activeTab === 'inconclusive'
                      ? 'border-[#E5A96A] text-[#E5A96A]'
                      : 'border-transparent text-[#727780] hover:text-[#F3F4F6]'
                  }`}
                >
                  Inconclusive ({comparison.summary.inconclusiveCount})
                </button>
                <button
                  onClick={() => setActiveTab('measurements')}
                  className={`px-3 py-2 border-b-2 transition-colors ${
                    activeTab === 'measurements'
                      ? 'border-[#D8E7A2] text-[#D8E7A2]'
                      : 'border-transparent text-[#727780] hover:text-[#F3F4F6]'
                  }`}
                >
                  Technical Telemetry ({comparison.measurements.length})
                </button>
              </div>

              {/* Technical Telemetry Table */}
              {activeTab === 'measurements' && (
                <div className="rounded-lg border border-[#2B2F36] bg-[#17191C] overflow-hidden">
                  <div className="px-4 py-3 border-b border-[#24272D] bg-[#1A1C20] flex items-center justify-between">
                    <span className="text-[12px] font-semibold text-[#F3F4F6]">
                      Comparable Technical Measurements
                    </span>
                    <span className="text-[11px] text-[#727780] font-mono">
                      Safe calculations without arithmetic false positives
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-[12px]">
                      <thead>
                        <tr className="border-b border-[#24272D] bg-[#141618] text-[#727780] font-mono text-[11px]">
                          <th className="py-2.5 px-4">Metric</th>
                          <th className="py-2.5 px-4">Older Audit ({comparison.olderTimestamp.substring(0, 10)})</th>
                          <th className="py-2.5 px-4">Newer Audit ({comparison.newerTimestamp.substring(0, 10)})</th>
                          <th className="py-2.5 px-4">Delta / % Change</th>
                          <th className="py-2.5 px-4">Assessment</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#22252A] font-mono text-[12px]">
                        {comparison.measurements.map((m) => {
                          const isComp = m.status === 'comparable';
                          return (
                            <tr key={m.key} className="hover:bg-[#1A1C20] transition-colors">
                              <td className="py-3 px-4 font-sans font-medium text-[#F3F4F6]">
                                <div>{m.label}</div>
                                {m.reason && (
                                  <div className="text-[10px] text-[#E5A96A] font-sans font-normal mt-0.5">
                                    {m.reason}
                                  </div>
                                )}
                              </td>
                              <td className="py-3 px-4 text-[#A0A5AD]">
                                {m.before !== null && m.before !== undefined ? `${m.before} ${m.unit || ''}` : 'N/A'}
                              </td>
                              <td className="py-3 px-4 text-[#F3F4F6] font-semibold">
                                {m.after !== null && m.after !== undefined ? `${m.after} ${m.unit || ''}` : 'N/A'}
                              </td>
                              <td className="py-3 px-4">
                                {isComp && m.change !== null && m.change !== undefined ? (
                                  <span className={m.direction === 'improved' ? 'text-[#D8E7A2]' : (m.direction === 'degraded' ? 'text-[#E58080]' : 'text-[#727780]')}>
                                    {m.change > 0 ? `+${m.change}` : m.change} {m.unit || ''}
                                    {m.changePercent !== null && m.changePercent !== undefined && ` (${m.changePercent > 0 ? `+${m.changePercent}` : m.changePercent}%)`}
                                  </span>
                                ) : (
                                  <span className="text-[#555A64] text-[11px]">—</span>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                {m.status === 'inconclusive' ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-sans px-2 py-0.5 rounded bg-[#272118] text-[#E5A96A] border border-[#483B25]">
                                    Inconclusive
                                  </span>
                                ) : m.status === 'not_comparable' ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-sans px-2 py-0.5 rounded bg-[#202328] text-[#727780] border border-[#2E333C]">
                                    Not Comparable
                                  </span>
                                ) : m.direction === 'improved' ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-sans px-2 py-0.5 rounded bg-[#1C261B] text-[#D8E7A2] border border-[#3E4E30]">
                                    <ArrowUpRight className="w-3 h-3" /> Improved
                                  </span>
                                ) : m.direction === 'degraded' ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-sans px-2 py-0.5 rounded bg-[#291B1C] text-[#E58080] border border-[#5E2B2D]">
                                    <ArrowDownRight className="w-3 h-3" /> Regressed
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-sans px-2 py-0.5 rounded bg-[#1B1D20] text-[#A0A5AD] border border-[#2A2E35]">
                                    <Minus className="w-3 h-3" /> Unchanged
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Findings List */}
              {activeTab !== 'measurements' && (
                <div className="flex flex-col gap-4">
                  {/* Category Sections or Filtered List */}
                  {['resolved', 'new', 'persistent', 'inconclusive'].map((stateGroup) => {
                    if (activeTab !== 'all' && activeTab !== stateGroup) return null;

                    let items: FindingComparisonItem[] = [];
                    let headerLabel = '';
                    let headerColor = '';
                    let stateIcon = null;

                    if (stateGroup === 'resolved') {
                      items = comparison.resolvedFindings;
                      headerLabel = `Confirmed Resolved Issues (${items.length})`;
                      headerColor = 'text-[#88B87A] border-[#2C3B24] bg-[#162014]';
                      stateIcon = <CheckCircle2 className="w-4 h-4 text-[#88B87A]" />;
                    } else if (stateGroup === 'new') {
                      items = comparison.newFindings;
                      headerLabel = `Newly Detected Issues (${items.length})`;
                      headerColor = 'text-[#E58080] border-[#4A2628] bg-[#221314]';
                      stateIcon = <AlertCircle className="w-4 h-4 text-[#E58080]" />;
                    } else if (stateGroup === 'persistent') {
                      items = comparison.persistentFindings;
                      headerLabel = `Persistent Underlying Issues (${items.length})`;
                      headerColor = 'text-[#A0A5AD] border-[#2E333C] bg-[#181B1E]';
                      stateIcon = <Layers className="w-4 h-4 text-[#A0A5AD]" />;
                    } else if (stateGroup === 'inconclusive') {
                      items = comparison.inconclusiveFindings;
                      headerLabel = `Inconclusive Checks & Insufficient Evidence (${items.length})`;
                      headerColor = 'text-[#E5A96A] border-[#443720] bg-[#201A12]';
                      stateIcon = <HelpCircle className="w-4 h-4 text-[#E5A96A]" />;
                    }

                    if (items.length === 0 && activeTab === 'all') return null;

                    return (
                      <div key={stateGroup} className="flex flex-col gap-3">
                        <div className={`px-4 py-2.5 rounded border flex items-center justify-between ${headerColor}`}>
                          <div className="flex items-center gap-2 text-[12px] font-semibold">
                            {stateIcon}
                            <span>{headerLabel}</span>
                          </div>
                          <span className="text-[11px] font-mono opacity-80">
                            {stateGroup.toUpperCase()}
                          </span>
                        </div>

                        {items.length === 0 ? (
                          <div className="p-4 rounded border border-[#23262B] bg-[#151719] text-[12px] text-[#727780] italic">
                            No {stateGroup} findings recorded in this comparison.
                          </div>
                        ) : (
                          <div className="grid grid-cols-1 gap-3">
                            {items.map((item, idx) => (
                              <div
                                key={`${item.checkKey}-${idx}`}
                                className="rounded-lg border border-[#2B2F36] bg-[#17191C] p-4 flex flex-col gap-3 text-[12px]"
                              >
                                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[#23262B] pb-2.5">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-[#F3F4F6] text-[13px]">
                                      {item.title}
                                    </span>
                                    <span className="font-mono text-[10px] text-[#727780] bg-[#111214] px-2 py-0.5 rounded border border-[#25282F]">
                                      {item.checkKey}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2 shrink-0">
                                    <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-[#1A1C20] border border-[#2F343E] text-[#A0A5AD]">
                                      {item.category}
                                    </span>
                                    <Badge variant="severity" severity={item.severity} size="sm" />
                                  </div>
                                </div>

                                {/* Deterministic Decision Rationale */}
                                <div className="p-2.5 rounded bg-[#121416] border border-[#25282F] text-[11px] leading-relaxed">
                                  <strong className="text-[#A0A5AD] font-medium mr-1.5">Classification Rationale:</strong>
                                  <span className={item.state === 'resolved' ? 'text-[#88B87A]' : (item.state === 'new' ? 'text-[#E58080]' : (item.state === 'inconclusive' ? 'text-[#E5A96A]' : 'text-[#D0D4DC]'))}>
                                    {item.reason}
                                  </span>
                                </div>

                                {/* Evidence Comparison */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                                  {/* Older Evidence */}
                                  <div className="flex flex-col gap-1.5 p-3 rounded bg-[#121416] border border-[#24272D]">
                                    <div className="flex items-center justify-between text-[11px] text-[#727780] font-mono">
                                      <span>OLDER AUDIT ({comparison.olderTimestamp.substring(0, 10)})</span>
                                      {item.olderFindingId && <span className="text-[#4E5460]">ID: {item.olderFindingId}</span>}
                                    </div>
                                    <div className="text-[11px] text-[#A0A5AD] font-mono whitespace-pre-wrap line-clamp-3">
                                      {item.olderEvidence || item.olderObserved || 'Check omitted or no baseline evidence recorded.'}
                                    </div>
                                  </div>

                                  {/* Newer Evidence */}
                                  <div className="flex flex-col gap-1.5 p-3 rounded bg-[#121416] border border-[#24272D]">
                                    <div className="flex items-center justify-between text-[11px] text-[#727780] font-mono">
                                      <span>NEWER AUDIT ({comparison.newerTimestamp.substring(0, 10)})</span>
                                      {item.newerFindingId && <span className="text-[#4E5460]">ID: {item.newerFindingId}</span>}
                                    </div>
                                    <div className="text-[11px] text-[#A0A5AD] font-mono whitespace-pre-wrap line-clamp-3">
                                      {item.newerEvidence || item.newerObserved || 'No evidence recorded in newer audit.'}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}

        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-[#24272D] bg-[#17191C] flex items-center justify-between text-[12px] text-[#727780] shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#D8E7A2]" />
            <span>Deterministic evidence comparator · Zero external AI calls · Zero live email dispatch</span>
          </div>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close Dossier
          </Button>
        </div>

      </div>
    </div>
  );
};
