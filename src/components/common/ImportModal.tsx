import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Button } from './Button';
import { 
  X, 
  UploadCloud, 
  FileSpreadsheet, 
  AlertCircle, 
  Check, 
  Copy, 
  ArrowRight, 
  Layers, 
  AlertTriangle,
  RotateCcw
} from 'lucide-react';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SAMPLE_CSV = `Business Name,Category,City,State,Website URL,Email,Phone,Opportunity Score
Northstar Spatial Studio,Interior design,Navi Mumbai,Maharashtra,https://northstarspatial.in,studio@northstar.in,+91 22 2788 1234,88
Zenith Metal Crafts,Manufacturing,Thane,Maharashtra,https://zenithmetalcrafts.co.in,inquiry@zenith.co.in,+91 22 2544 5678,74
Sutra Design Lab,Architecture,Pune,Maharashtra,,,+91 20 6645 1122,92
Matrix Toolings,Industrial,Panvel,Maharashtra,https://matrixtoolings.com,ops@matrixtoolings.com,,68`;

interface PreviewItem {
  row_number: number;
  name: string;
  category: string;
  city: string;
  state: string;
  country: string;
  website_url?: string;
  website_status: string;
  phone?: string;
  email?: string;
  opportunity_score: number;
  is_duplicate: boolean;
  duplicate_reason?: string;
  existing_id?: string;
}

interface InvalidItem {
  row_number: number;
  error: string;
  raw_data: Record<string, any>;
}

export const ImportModal: React.FC<ImportModalProps> = ({ isOpen, onClose }) => {
  const { addToast, refreshProspects } = useApp();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [csvContent, setCsvContent] = useState('');
  const [step, setStep] = useState<'input' | 'preview'>('input');
  const [isLoading, setIsLoading] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Preview state from backend API
  const [headers, setHeaders] = useState<string[]>([]);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [previewRecords, setPreviewRecords] = useState<PreviewItem[]>([]);
  const [invalidRecords, setInvalidRecords] = useState<InvalidItem[]>([]);
  const [duplicateCount, setDuplicateCount] = useState(0);
  const [skipDuplicates, setSkipDuplicates] = useState(true);

  if (!isOpen) return null;

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      setCsvContent(text);
      setError(null);
    };
    reader.onerror = () => {
      setError('Failed to read uploaded CSV file.');
    };
    reader.readAsText(file);
  };

  const handlePreview = async () => {
    if (!csvContent.trim()) {
      setError('Please paste or upload CSV content first.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/prospects/import/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          csvContent,
          columnMapping: Object.keys(columnMapping).length > 0 ? columnMapping : undefined
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Preview failed with status ${response.status}`);
      }

      const data = await response.json();
      setHeaders(data.headers || []);
      setColumnMapping(data.column_mapping || {});
      setPreviewRecords(data.preview_records || []);
      setInvalidRecords(data.invalid_records || []);
      setDuplicateCount(data.duplicate_count || 0);
      setStep('preview');
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred parsing CSV.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (previewRecords.length === 0) {
      setError('No valid records available to import.');
      return;
    }

    setIsCommitting(true);
    setError(null);

    try {
      // Map preview records to confirm payload
      const recordsToCommit = previewRecords.map((r) => ({
        name: r.name,
        category: r.category,
        city: r.city,
        state: r.state,
        country: r.country,
        website_url: r.website_url,
        website_status: r.website_status,
        phone: r.phone,
        email: r.email,
        opportunity_score: r.opportunity_score
      }));

      const response = await fetch('/api/prospects/import/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          records: recordsToCommit,
          skipDuplicates
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Import failed with status ${response.status}`);
      }

      const summary = await response.json();
      await refreshProspects();

      addToast(
        `Imported ${summary.imported_count} prospects successfully (${summary.skipped_duplicates_count} duplicates skipped).`,
        'success'
      );
      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to commit imported records.');
    } finally {
      setIsCommitting(false);
    }
  };

  const handleClose = () => {
    setCsvContent('');
    setStep('input');
    setPreviewRecords([]);
    setInvalidRecords([]);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div 
        className="w-full max-w-4xl rounded-lg border border-[#30343A] bg-[#17191C] shadow-2xl overflow-hidden flex flex-col max-h-[88vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#24272D] bg-[#141619]">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded bg-[#1D2024] border border-[#30343A]">
              <FileSpreadsheet className="w-4 h-4 text-[#D8E7A2]" />
            </div>
            <div>
              <h3 className="text-[14px] font-medium text-[#F3F4F6]">
                Import Prospects via CSV
              </h3>
              <p className="text-[12px] text-[#727780]">
                {step === 'input' 
                  ? 'Step 1: Select CSV file or paste spreadsheet data' 
                  : 'Step 2: Preview validated records and duplicate analysis'}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded text-[#727780] hover:text-[#F3F4F6] hover:bg-[#202328]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 flex-1 overflow-y-auto flex flex-col gap-4">
          {error && (
            <div className="flex items-center gap-2 p-3 rounded bg-[#2A1818] border border-[#4A2626] text-[12px] text-[#D78383]">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {step === 'input' ? (
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <span className="text-[12px] font-medium text-[#A0A5AD]">
                  Select CSV File or Paste RFC-4180 Data
                </span>
                <div className="flex items-center gap-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".csv,text/csv"
                    className="hidden"
                  />
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    leftIcon={<UploadCloud className="w-3.5 h-3.5" />}
                  >
                    Choose CSV File
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setCsvContent(SAMPLE_CSV);
                      setError(null);
                    }}
                    leftIcon={<Copy className="w-3.5 h-3.5" />}
                  >
                    Load Sample
                  </Button>
                </div>
              </div>

              <textarea
                value={csvContent}
                onChange={(e) => setCsvContent(e.target.value)}
                rows={8}
                placeholder="Business Name,Category,City,State,Website URL,Opportunity Score&#10;Acme Industrial,Manufacturing,Navi Mumbai,Maharashtra,https://acme.in,85"
                className="w-full bg-[#111214] border border-[#30343A] rounded p-3 text-[12px] font-mono text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />

              <div className="p-3 rounded bg-[#1A1C20] border border-[#262A30] flex flex-col gap-1.5 text-[11px] text-[#727780]">
                <span className="font-medium text-[#A0A5AD] flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-[#D8E7A2]" /> CSV Import Guarantees & Protections:
                </span>
                <ul className="list-disc list-inside space-y-0.5 text-[#727780]">
                  <li>Supports quoted fields with embedded commas and Unicode characters (UTF-8).</li>
                  <li>Automatic Spreadsheet Formula Injection defense (sanitizes <code>=, +, -, @</code>).</li>
                  <li>Deterministic duplicate prevention checks active SQLite database by name, location, and website domain.</li>
                  <li>No database changes occur until you confirm the previewed records.</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {/* Summary Metrics */}
              <div className="grid grid-cols-4 gap-2.5">
                <div className="p-3 rounded bg-[#1A1C20] border border-[#2B2F36]">
                  <div className="text-[11px] text-[#727780]">Total Rows</div>
                  <div className="text-[18px] font-semibold text-[#F3F4F6] font-mono mt-0.5">
                    {previewRecords.length + invalidRecords.length}
                  </div>
                </div>

                <div className="p-3 rounded bg-[#18261F] border border-[#253E31]">
                  <div className="text-[11px] text-[#80B89A]">Valid Records</div>
                  <div className="text-[18px] font-semibold text-[#80B89A] font-mono mt-0.5">
                    {previewRecords.length}
                  </div>
                </div>

                <div className="p-3 rounded bg-[#2A2417] border border-[#4A3D22]">
                  <div className="text-[11px] text-[#D8B16C]">Duplicates Found</div>
                  <div className="text-[18px] font-semibold text-[#D8B16C] font-mono mt-0.5">
                    {duplicateCount}
                  </div>
                </div>

                <div className="p-3 rounded bg-[#2A1818] border border-[#4A2626]">
                  <div className="text-[11px] text-[#D78383]">Invalid Rows</div>
                  <div className="text-[18px] font-semibold text-[#D78383] font-mono mt-0.5">
                    {invalidRecords.length}
                  </div>
                </div>
              </div>

              {/* Duplicate settings */}
              {duplicateCount > 0 && (
                <div className="flex items-center gap-2 p-2.5 rounded bg-[#2A2417]/60 border border-[#4A3D22] text-[12px] text-[#D8B16C]">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <div className="flex-1">
                    {duplicateCount} row(s) match existing records in your prospect pipeline.
                  </div>
                  <label className="flex items-center gap-1.5 cursor-pointer select-none text-[#F3F4F6] text-[11px]">
                    <input
                      type="checkbox"
                      checked={skipDuplicates}
                      onChange={(e) => setSkipDuplicates(e.target.checked)}
                      className="rounded border-[#4B5361] bg-[#111214] text-[#D8E7A2] focus:ring-0"
                    />
                    Skip duplicates (Recommended)
                  </label>
                </div>
              )}

              {/* Valid records preview table */}
              <div className="flex flex-col gap-1.5">
                <span className="text-[12px] font-medium text-[#A0A5AD]">
                  Previewing Valid Records ({previewRecords.length}):
                </span>
                <div className="rounded border border-[#2B2F36] overflow-hidden max-h-52 overflow-y-auto">
                  <table className="w-full text-left text-[12px]">
                    <thead className="bg-[#1D2024] text-[#727780] border-b border-[#2B2F36] sticky top-0">
                      <tr>
                        <th className="py-2 px-3 font-medium">Row</th>
                        <th className="py-2 px-3 font-medium">Business</th>
                        <th className="py-2 px-3 font-medium">Category</th>
                        <th className="py-2 px-3 font-medium">Location</th>
                        <th className="py-2 px-3 font-medium">Website</th>
                        <th className="py-2 px-3 font-medium">Duplicate Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#23272D] bg-[#141618]">
                      {previewRecords.map((r) => (
                        <tr key={r.row_number} className="hover:bg-[#1A1D21]">
                          <td className="py-1.5 px-3 font-mono text-[11px] text-[#727780]">
                            #{r.row_number}
                          </td>
                          <td className="py-1.5 px-3 text-[#F3F4F6] font-medium">
                            {r.name}
                          </td>
                          <td className="py-1.5 px-3 text-[#A0A5AD]">{r.category}</td>
                          <td className="py-1.5 px-3 text-[#A0A5AD]">{r.city}, {r.state}</td>
                          <td className="py-1.5 px-3 font-mono text-[11px] text-[#A0A5AD]">
                            {r.website_url || <span className="text-[#727780]">None</span>}
                          </td>
                          <td className="py-1.5 px-3">
                            {r.is_duplicate ? (
                              <span 
                                title={r.duplicate_reason}
                                className="inline-flex items-center gap-1 font-mono text-[10px] text-[#D8B16C] bg-[#2A2417] px-1.5 py-0.5 rounded border border-[#4A3D22]"
                              >
                                <AlertTriangle className="w-3 h-3" /> Duplicate
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 font-mono text-[10px] text-[#80B89A] bg-[#18261F] px-1.5 py-0.5 rounded border border-[#253E31]">
                                <Check className="w-3 h-3" /> Valid
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Invalid records list */}
              {invalidRecords.length > 0 && (
                <div className="flex flex-col gap-1.5">
                  <span className="text-[12px] font-medium text-[#D78383] flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5" /> Invalid Rows ({invalidRecords.length}) — Will be skipped:
                  </span>
                  <div className="rounded border border-[#4A2626] bg-[#221515] p-2 max-h-28 overflow-y-auto text-[11px] divide-y divide-[#3A1E1E]">
                    {invalidRecords.map((inv) => (
                      <div key={inv.row_number} className="py-1 flex items-center justify-between text-[#D78383]">
                        <span><strong>Row #{inv.row_number}:</strong> {inv.error}</span>
                        <span className="font-mono text-[#727780]">{JSON.stringify(inv.raw_data)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-[#24272D] bg-[#141619]">
          {step === 'preview' ? (
            <Button
              variant="secondary"
              size="md"
              onClick={() => setStep('input')}
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              Adjust Input Data
            </Button>
          ) : (
            <div className="text-[12px] text-[#727780]">
              Ready to parse RFC-4180 CSV
            </div>
          )}

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="md" onClick={handleClose}>
              Cancel
            </Button>

            {step === 'input' ? (
              <Button
                variant="primary"
                size="md"
                disabled={!csvContent.trim()}
                isLoading={isLoading}
                onClick={handlePreview}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Analyze & Preview
              </Button>
            ) : (
              <Button
                variant="primary"
                size="md"
                disabled={previewRecords.length === 0}
                isLoading={isCommitting}
                onClick={handleConfirmImport}
                leftIcon={<UploadCloud className="w-4 h-4" />}
              >
                Confirm & Import ({skipDuplicates ? previewRecords.filter(r => !r.is_duplicate).length : previewRecords.length})
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
