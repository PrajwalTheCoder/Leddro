import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Building2, 
  FileText, 
  Mail, 
  Compass, 
  Layers, 
  History, 
  Settings, 
  UploadCloud, 
  Play,
  ArrowRight,
  X
} from 'lucide-react';
import { Badge } from './Badge';
import logoImg from '../../assets/logo.png';
import nameLogoImg from '../../assets/leddro-name-logo.png';

export const CommandPalette: React.FC = () => {
  const { 
    isCommandPaletteOpen, 
    setIsCommandPaletteOpen, 
    prospects, 
    setSelectedProspectId,
    selectedProspect,
    runAudit,
    createEmailDraftForProspect,
    backendOnline
  } = useApp();
  
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (isCommandPaletteOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isCommandPaletteOpen]);

  if (!isCommandPaletteOpen) return null;

  const filteredProspects = prospects.filter(
    (p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.category.toLowerCase().includes(query.toLowerCase()) ||
      p.location.city.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 5);

  const navigationActions = [
    { id: 'nav-overview', label: 'Go to Overview Dashboard', icon: <Layers className="w-4 h-4 text-[#A0A5AD]" />, path: '/app' },
    { id: 'nav-discover', label: 'Discover New Prospects', icon: <Compass className="w-4 h-4 text-[#A0A5AD]" />, path: '/discover' },
    { id: 'nav-prospects', label: 'Manage All Prospects', icon: <Building2 className="w-4 h-4 text-[#A0A5AD]" />, path: '/prospects' },
    { id: 'nav-audits', label: 'Website Audit Reports', icon: <FileText className="w-4 h-4 text-[#A0A5AD]" />, path: '/audits' },
    { id: 'nav-drafts', label: 'Email Draft Editor', icon: <Mail className="w-4 h-4 text-[#A0A5AD]" />, path: '/drafts' },
    { id: 'nav-history', label: 'Email Submission History', icon: <History className="w-4 h-4 text-[#A0A5AD]" />, path: '/history' },
    ...(backendOnline ? [
      { id: 'nav-integrations', label: 'Integrations & Gmail OAuth', icon: <Settings className="w-4 h-4 text-[#A0A5AD]" />, path: '/integrations' }
    ] : []),
  ].filter((a) => a.label.toLowerCase().includes(query.toLowerCase()));

  const allItems = [
    ...filteredProspects.map((p) => ({ type: 'prospect' as const, item: p })),
    ...navigationActions.map((n) => ({ type: 'nav' as const, item: n })),
  ];

  const handleSelect = (index: number) => {
    const selected = allItems[index];
    if (!selected) return;

    if (selected.type === 'prospect') {
      setSelectedProspectId(selected.item.id);
      setIsCommandPaletteOpen(false);
      navigate('/audits');
    } else if (selected.type === 'nav') {
      setIsCommandPaletteOpen(false);
      navigate(selected.item.path);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, allItems.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + allItems.length) % Math.max(1, allItems.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      handleSelect(selectedIndex);
    } else if (e.key === 'Escape') {
      setIsCommandPaletteOpen(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/70 backdrop-blur-none px-4">
      <div 
        className="w-full max-w-xl rounded border border-[#30343A] bg-[#17191C] shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center px-4 py-3 border-b border-[#25282E] gap-3">
          <Search className="w-4 h-4 text-[#727780]" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Type a prospect name, command, or screen..."
            className="w-full bg-transparent text-[13px] text-[#F3F4F6] placeholder-[#727780] outline-none"
          />
          <button
            onClick={() => setIsCommandPaletteOpen(false)}
            className="p-1 rounded text-[#727780] hover:text-[#F3F4F6]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* List of results */}
        <div className="max-h-80 overflow-y-auto p-2 divide-y divide-[#22252B]">
          {filteredProspects.length > 0 && (
            <div className="pb-2">
              <div className="px-2 py-1 text-[11px] font-medium text-[#727780] uppercase tracking-wider">
                Prospects
              </div>
              {filteredProspects.map((p, idx) => {
                const isSelected = selectedIndex === idx;
                return (
                  <div
                    key={p.id}
                    onClick={() => {
                      setSelectedProspectId(p.id);
                      setIsCommandPaletteOpen(false);
                      navigate('/audits');
                    }}
                    onMouseEnter={() => setSelectedIndex(idx)}
                    className={`flex items-center justify-between px-2.5 py-2 rounded cursor-pointer transition-colors ${
                      isSelected ? 'bg-[#24272C] text-[#F3F4F6]' : 'text-[#A0A5AD] hover:bg-[#1D2024]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Building2 className="w-4 h-4 text-[#727780] shrink-0" />
                      <div className="truncate">
                        <span className="text-[13px] font-medium text-[#F3F4F6] mr-2">
                          {p.name}
                        </span>
                        <span className="text-[12px] text-[#727780]">
                          {p.category} · {p.location.city}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant="website" websiteStatus={p.websiteStatus} size="sm" />
                      <span className="text-[11px] font-mono text-[#D8E7A2] bg-[#22271B] px-1.5 py-0.5 rounded border border-[#374026]">
                        {p.opportunityScore}/100
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {navigationActions.length > 0 && (
            <div className="pt-2">
              <div className="px-2 py-1 text-[11px] font-medium text-[#727780] uppercase tracking-wider">
                Commands &amp; Navigation
              </div>
              {navigationActions.map((n, idx) => {
                const itemIdx = filteredProspects.length + idx;
                const isSelected = selectedIndex === itemIdx;
                return (
                  <div
                    key={n.id}
                    onClick={() => {
                      setIsCommandPaletteOpen(false);
                      navigate(n.path);
                    }}
                    onMouseEnter={() => setSelectedIndex(itemIdx)}
                    className={`flex items-center justify-between px-2.5 py-2 rounded cursor-pointer transition-colors ${
                      isSelected ? 'bg-[#24272C] text-[#F3F4F6]' : 'text-[#A0A5AD] hover:bg-[#1D2024]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      {n.icon}
                      <span className="text-[13px] text-[#F3F4F6]">{n.label}</span>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-[#727780]" />
                  </div>
                );
              })}
            </div>
          )}

          {allItems.length === 0 && (
            <div className="py-8 text-center text-[12px] text-[#727780]">
              No prospects or commands found for "{query}"
            </div>
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="flex items-center justify-between px-3.5 py-2 bg-[#131417] border-t border-[#25282E] text-[11px] text-[#727780]">
          <div className="flex items-center gap-3">
            <span><kbd className="px-1.5 py-0.5 rounded bg-[#1D2024] border border-[#30343A] text-[#A0A5AD]">↑↓</kbd> navigate</span>
            <span><kbd className="px-1.5 py-0.5 rounded bg-[#1D2024] border border-[#30343A] text-[#A0A5AD]">↵</kbd> select</span>
            <span><kbd className="px-1.5 py-0.5 rounded bg-[#1D2024] border border-[#30343A] text-[#A0A5AD]">esc</kbd> close</span>
          </div>
          <div className="flex items-center gap-2">
            <img src={logoImg} alt="Leddro Mark" className="w-4 h-4 object-contain" />
            <img src={nameLogoImg} alt="Leddro" className="h-4.5 w-auto object-contain" />
            <span className="font-mono text-[#D8E7A2]/80 text-[10px]">Query v2.4</span>
          </div>
        </div>
      </div>
    </div>
  );
};
