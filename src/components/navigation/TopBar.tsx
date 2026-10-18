import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Search, 
  Bell, 
  ChevronDown, 
  ShieldCheck, 
  Sparkles, 
  Activity, 
  CheckCircle2, 
  Mail, 
  Database,
  ExternalLink,
  Clock
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const TopBar: React.FC = () => {
  const { 
    prospects, 
    emailDrafts, 
    emailHistory, 
    activities, 
    setIsCommandPaletteOpen,
    integrations,
    backendOnline 
  } = useApp();

  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const notificationRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Metrics
  const totalCount = prospects.length;
  const auditedCount = prospects.filter((p) => p.auditCount > 0).length;
  const needsReviewCount = prospects.filter((p) => p.status === 'needs_review').length;
  const draftsCount = emailDrafts.length;
  const submittedCount = emailHistory.filter((h) => h.status === 'submitted').length;

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-14 border-b border-[#22252A] bg-[#111214] flex items-center justify-between px-6 shrink-0 z-20">
      {/* Left: Compact Status Indicators (Like Haulix Top Chips) */}
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17191C] border border-[#2B2F36] text-[12px] text-[#A0A5AD]">
          <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-[#D8E7A2]' : 'bg-[#E5A96A]'}`} />
          <span>Engine: <strong className="text-[#F3F4F6] font-medium">{backendOnline ? 'FastAPI Active' : 'Offline'}</strong></span>
        </div>

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17191C] border border-[#2B2F36] text-[12px] text-[#A0A5AD]">
          <Database className="w-3.5 h-3.5 text-[#80B89A]" />
          <span>Active: <strong className="text-[#F3F4F6] font-medium">{totalCount}</strong></span>
        </div>

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17191C] border border-[#2B2F36] text-[12px] text-[#A0A5AD]">
          <ShieldCheck className="w-3.5 h-3.5 text-[#91B7D8]" />
          <span>Audited: <strong className="text-[#F3F4F6] font-medium">{auditedCount}</strong></span>
        </div>

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17191C] border border-[#2B2F36] text-[12px] text-[#A0A5AD]">
          <span className="w-2 h-2 rounded-full bg-[#D8B16C]" />
          <span>Review: <strong className="text-[#F3F4F6] font-medium">{needsReviewCount}</strong></span>
        </div>

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17191C] border border-[#2B2F36] text-[12px] text-[#A0A5AD]">
          <Mail className="w-3.5 h-3.5 text-[#D8E7A2]" />
          <span>Drafts: <strong className="text-[#F3F4F6] font-medium">{draftsCount}</strong></span>
        </div>

        <div className="hidden lg:inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#17191C] border border-[#2B2F36] text-[12px] text-[#A0A5AD]">
          <Clock className="w-3.5 h-3.5 text-[#727780]" />
          <span>Submitted: <strong className="text-[#F3F4F6] font-medium">{submittedCount}</strong></span>
        </div>
      </div>

      {/* Right Controls: Search, Notification Bell, User Badge */}
      <div className="flex items-center gap-3">
        {/* Global Search pill with shortcut */}
        <button
          onClick={() => setIsCommandPaletteOpen(true)}
          className="flex items-center gap-3 px-3 py-1.5 rounded bg-[#17191C] border border-[#2B2F36] hover:border-[#3E444F] text-[12px] text-[#727780] hover:text-[#A0A5AD] transition-all w-52 sm:w-64"
        >
          <Search className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate text-left flex-1">Search prospects, URLs...</span>
          <kbd className="hidden sm:inline-block font-mono text-[10px] bg-[#22252B] text-[#A0A5AD] px-1.5 py-0.5 rounded border border-[#30343A]">
            ⌘K
          </kbd>
        </button>

        {/* Date Filter Selector Pill like screenshot */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-[#17191C] border border-[#2B2F36] text-[12px] text-[#A0A5AD]">
          <span>Last 7 days</span>
          <ChevronDown className="w-3.5 h-3.5 text-[#727780]" />
        </div>

        {/* Notification Bell */}
        <div className="relative" ref={notificationRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="w-8 h-8 rounded-full bg-[#17191C] border border-[#2B2F36] flex items-center justify-center text-[#A0A5AD] hover:text-[#F3F4F6] hover:bg-[#1E2126] transition-colors relative"
            aria-label="Recent Activities"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#D8B16C] text-[#111214] font-bold text-[10px] flex items-center justify-center">
              {activities.length > 9 ? '9+' : activities.length}
            </span>
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded border border-[#30343A] bg-[#17191C] shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-1">
              <div className="flex items-center justify-between px-3 py-2 border-b border-[#24272D]">
                <span className="text-[12px] font-medium text-[#F3F4F6]">Audit &amp; Dispatch Stream</span>
                <span className="text-[11px] font-mono text-[#D8E7A2]">Live</span>
              </div>
              <div className="max-h-72 overflow-y-auto divide-y divide-[#22252B]">
                {activities.slice(0, 6).map((act) => (
                  <div key={act.id} className="p-2.5 hover:bg-[#1E2126] rounded transition-colors text-[12px]">
                    <div className="flex items-center justify-between text-[#F3F4F6] font-medium mb-0.5">
                      <span className="truncate">{act.title}</span>
                      <span className="text-[10px] font-mono text-[#727780] shrink-0 ml-2">{act.timestamp}</span>
                    </div>
                    <p className="text-[11px] text-[#727780] line-clamp-2">{act.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Operator / Google Account Profile Chip */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 pl-1 pr-2.5 py-1 rounded bg-[#17191C] border border-[#2B2F36] hover:border-[#3E444F] transition-colors"
          >
            <div className={`w-6 h-6 rounded-full font-semibold text-[11px] flex items-center justify-center border ${
              integrations.gmail.isConnected
                ? 'bg-[#18261F] text-[#80B89A] border-[#253E31]'
                : 'bg-[#292D34] text-[#A0A5AD] border-[#3A404A]'
            }`}>
              {integrations.gmail.isConnected && integrations.gmail.connectedAccount
                ? integrations.gmail.connectedAccount[0].toUpperCase()
                : 'OP'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-[12px] font-medium text-[#F3F4F6] leading-none truncate max-w-[140px]">
                {integrations.gmail.isConnected && integrations.gmail.connectedAccount
                  ? integrations.gmail.connectedAccount.split('@')[0]
                  : 'Local Workspace'}
              </div>
              <div className="text-[10px] text-[#727780] leading-none mt-0.5">
                {integrations.gmail.isConnected ? 'Google Connected' : 'Not Connected'}
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[#727780]" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-64 rounded border border-[#30343A] bg-[#17191C] shadow-2xl p-2 z-50 text-[12px]">
              <div className="px-2.5 py-2 border-b border-[#24272D] mb-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[#F3F4F6]">
                    {integrations.gmail.isConnected ? 'Google Account' : 'Local Operator'}
                  </span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                    integrations.gmail.isConnected
                      ? 'bg-[#18261F] text-[#80B89A] border-[#253E31]'
                      : 'bg-[#212328] text-[#727780] border-[#30343A]'
                  }`}>
                    {integrations.gmail.isConnected ? 'Active' : 'Unlinked'}
                  </span>
                </div>
                <div className="text-[11px] text-[#A0A5AD] truncate mt-1">
                  {integrations.gmail.isConnected && integrations.gmail.connectedAccount
                    ? integrations.gmail.connectedAccount
                    : 'No Google account connected'}
                </div>
              </div>
              <button
                onClick={() => {
                  setShowUserMenu(false);
                  navigate('/integrations');
                }}
                className="w-full text-left px-2.5 py-1.5 rounded text-[#A0A5AD] hover:text-[#F3F4F6] hover:bg-[#1E2126] transition-colors"
              >
                Integrations &amp; OAuth
              </button>
              <div className="px-2.5 py-1 text-[11px] text-[#727780] flex items-center justify-between border-t border-[#24272D] mt-1 pt-1">
                <span>Outbound Gateway</span>
                <span className="font-mono text-[11px] text-[#80B89A] flex items-center gap-1">
                  {integrations.gmail.isConnected ? 'Gmail API OAuth' : 'Local Only'}
                </span>
              </div>
            </div>
          )}
        </div>

      </div>
    </header>
  );
};
