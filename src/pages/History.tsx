import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { 
  History as HistoryIcon, 
  Search, 
  Mail, 
  ExternalLink, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  X,
  Building2,
  FileText
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmailHistoryItem } from '../types';

export const History: React.FC = () => {
  const { emailHistory } = useApp();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedItem, setSelectedItem] = useState<EmailHistoryItem | null>(null);

  const filtered = emailHistory.filter((item) => {
    const matchesSearch = 
      item.recipient.toLowerCase().includes(search.toLowerCase()) ||
      item.prospectName.toLowerCase().includes(search.toLowerCase()) ||
      item.subject.toLowerCase().includes(search.toLowerCase());
    if (!matchesSearch) return false;

    if (statusFilter !== 'all' && item.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#111214]">
      {/* Header */}
      <div className="px-6 pt-5 pb-3 border-b border-[#22252A] flex flex-col gap-3 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-[24px] font-semibold text-[#F3F4F6] tracking-tight">
              Email Dispatch History
            </h1>
            <p className="text-[12px] text-[#A0A5AD] mt-0.5">
              Deterministic log of all authorized outbound messages and provider gateway receipts.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="w-3.5 h-3.5 text-[#727780] absolute left-3 top-2.5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search recipient or subject..."
                className="w-full bg-[#17191C] border border-[#2B2F36] rounded pl-9 pr-3 py-1.5 text-[12px] text-[#F3F4F6] placeholder-[#575C66] focus:border-[#4B5361] outline-none"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#17191C] border border-[#2B2F36] rounded px-2.5 py-1.5 text-[12px] text-[#A0A5AD] focus:border-[#4B5361] outline-none"
            >
              <option value="all">All Dispatches</option>
              <option value="submitted">Submitted / Sent</option>
              <option value="uncertain">Uncertain (Network Timeout)</option>
              <option value="failed">Failed</option>
              <option value="awaiting_approval">Awaiting Approval</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="flex-1 overflow-hidden p-6">
        <div className="h-full flex flex-col rounded border border-[#282B31] bg-[#17191C] overflow-hidden">
          <div className="px-4 py-2 border-b border-[#24272D] flex items-center justify-between text-[12px] text-[#A0A5AD] bg-[#1A1C20]">
            <span>Showing <strong>{filtered.length}</strong> logged email dispatches</span>
            <span className="font-mono text-[11px] text-[#727780]">Provider verification: Server Accepted</span>
          </div>

          <div className="flex-1 overflow-y-auto">
            <table className="w-full text-left border-collapse text-[12px]">
              <thead className="sticky top-0 bg-[#1A1C20] text-[#727780] font-medium border-b border-[#24272D] z-10">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Recipient</th>
                  <th className="py-2.5 px-3 font-medium">Prospect Entity</th>
                  <th className="py-2.5 px-3 font-medium">Subject</th>
                  <th className="py-2.5 px-3 font-medium">Dispatch Date</th>
                  <th className="py-2.5 px-3 font-medium">Provider Gateway</th>
                  <th className="py-2.5 px-3 font-medium">Status</th>
                  <th className="py-2.5 px-4 text-right font-medium">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202328] bg-[#17191C]">
                {filtered.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => setSelectedItem(item)}
                    className="hover:bg-[#1C1F24] cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono text-[12px] text-[#F3F4F6]">
                      {item.recipient}
                    </td>

                    <td className="py-3 px-3 text-[#A0A5AD]">
                      <div className="flex items-center gap-1.5 font-medium text-[#D6D9E0]">
                        <Building2 className="w-3.5 h-3.5 text-[#727780]" />
                        <span>{item.prospectName}</span>
                      </div>
                    </td>

                    <td className="py-3 px-3 text-[#F3F4F6] max-w-xs truncate">
                      {item.subject}
                    </td>

                    <td className="py-3 px-3 font-mono text-[11px] text-[#727780]">
                      {item.date}
                    </td>

                    <td className="py-3 px-3 font-mono text-[11px] text-[#A0A5AD]">
                      {item.provider}
                    </td>

                    <td className="py-3 px-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border ${
                        item.status === 'submitted' || item.status === 'sent'
                          ? 'bg-[#18261F] text-[#80B89A] border-[#253D30]'
                          : item.status === 'failed'
                          ? 'bg-[#2A1818] text-[#D78383] border-[#4A2626]'
                          : item.status === 'uncertain'
                          ? 'bg-[#2C2415] text-[#E5A93C] border-[#52411E]'
                          : 'bg-[#2A2417] text-[#D8B16C] border-[#4A3D22]'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          item.status === 'submitted' || item.status === 'sent'
                            ? 'bg-[#80B89A]'
                            : item.status === 'failed'
                            ? 'bg-[#D78383]'
                            : item.status === 'uncertain'
                            ? 'bg-[#E5A93C]'
                            : 'bg-[#D8B16C]'
                        }`} />
                        {item.status.toUpperCase()}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right">
                      <Button variant="ghost" size="sm">
                        Inspect
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Item Inspection Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-lg rounded border border-[#30343A] bg-[#17191C] shadow-2xl p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-[#24272D] pb-3">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-[#D8E7A2]" />
                <h3 className="text-[14px] font-medium text-[#F3F4F6]">Outbound Dispatch Receipt</h3>
              </div>
              <button onClick={() => setSelectedItem(null)} className="text-[#727780] hover:text-[#F3F4F6]">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-col gap-3 text-[12px]">
              <div className="p-3 rounded bg-[#111214] border border-[#24272D] flex flex-col gap-1.5 font-mono text-[11px] text-[#A0A5AD]">
                <div>Target Entity: <span className="text-[#F3F4F6]">{selectedItem.prospectName}</span></div>
                <div>Recipient: <span className="text-[#F3F4F6]">{selectedItem.recipient}</span></div>
                <div>Subject: <span className="text-[#F3F4F6]">{selectedItem.subject}</span></div>
                <div>Gmail Message ID: <span className="text-[#D8E7A2]">{selectedItem.providerMessageId || 'N/A (Pending confirmation)'}</span></div>
                <div>Status: <span className="text-[#80B89A]">{selectedItem.status.toUpperCase()}</span> (Submitted to MTA)</div>
              </div>

              <div>
                <div className="text-[11px] font-medium text-[#727780] uppercase tracking-wider mb-1">
                  Message Excerpt
                </div>
                <div className="p-3 rounded bg-[#111214] border border-[#24272D] text-[12px] text-[#D6D9E0] leading-relaxed">
                  {selectedItem.bodySnippet}
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#24272D]">
              <Button variant="secondary" size="md" onClick={() => setSelectedItem(null)}>
                Close Receipt
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
