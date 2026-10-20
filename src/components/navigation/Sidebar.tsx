import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  Layers, 
  Compass, 
  Building2, 
  FileCode2, 
  Mail, 
  History, 
  Puzzle, 
  Settings, 
  HelpCircle,
  ExternalLink,
  Sparkles,
  X
} from 'lucide-react';
import logoImg from '../../assets/logo.png';
import nameLogoImg from '../../assets/leddro-name-logo.png';

interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

import { useApp } from '../../context/AppContext';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const { backendOnline } = useApp();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [showHelpModal, setShowHelpModal] = useState(false);

  const isHostedDemo = typeof window !== 'undefined' && (
    window.location.hostname.includes('github.io') ||
    window.location.hostname.includes('vercel.app') ||
    window.location.hostname.includes('pages.dev')
  );

  const mainNavItems: NavItem[] = [
    { id: 'overview', label: 'Overview', path: '/', icon: Layers },
    { id: 'discover', label: 'Discover', path: '/discover', icon: Compass },
    { id: 'prospects', label: 'Prospects', path: '/prospects', icon: Building2 },
    { id: 'audits', label: 'Audits', path: '/audits', icon: FileCode2 },
    { id: 'drafts', label: 'Email Drafts', path: '/drafts', icon: Mail },
    { id: 'history', label: 'Email History', path: '/history', icon: History },
  ];

  const bottomNavItems: NavItem[] = [
    ...(isHostedDemo ? [{ id: 'landing', label: 'Showcase & Demo Video', path: '/landing', icon: Sparkles }] : []),
    ...(!isHostedDemo || backendOnline ? [
      { id: 'integrations', label: 'Integrations', path: '/integrations', icon: Puzzle },
      { id: 'settings', label: 'Settings', path: '/integrations', icon: Settings },
    ] : [])
  ];

  return (
    <>
      <aside 
        className="w-[72px] shrink-0 bg-[#111214] border-r border-[#22252A] flex flex-col items-center justify-between py-4 select-none z-30"
        aria-label="Main Navigation Rail"
      >
        {/* Top Product Logo Symbol */}
        <div className="flex flex-col items-center gap-6">
          <NavLink to="/" className="relative group">
            <div className="w-10 h-10 rounded-xl bg-[#111214] border border-[#30343A] flex items-center justify-center cursor-pointer transition-all hover:border-[#D8E7A2]/60 overflow-hidden p-1 shadow-[0_0_12px_rgba(216,231,162,0.2)]">
              <img src={logoImg} alt="Leddro Intelligence" className="w-full h-full object-contain rounded-lg" />
            </div>
            {/* Tooltip */}
            <div className="absolute left-[78px] top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-2 px-3 py-1.5 rounded bg-[#24272C] border border-[#30343A] text-[12px] font-medium text-[#F3F4F6] whitespace-nowrap shadow-xl z-50 pointer-events-none">
              <img src={nameLogoImg} alt="Leddro" className="h-4.5 w-auto object-contain" />
              <span className="text-[11px] text-[#A0A5AD]">Intelligence (Home)</span>
            </div>
          </NavLink>

          {/* Navigation Rail Items */}
          <nav className="flex flex-col items-center gap-2">
            {mainNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = (item.path === '/' || item.path === '/app')
                ? (location.pathname === '/' || location.pathname === '/app')
                : location.pathname.startsWith(item.path);

              return (
                <div 
                  key={item.id} 
                  className="relative"
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
                >
                  <NavLink
                    to={item.path}
                    aria-label={item.label}
                    className={`w-11 h-11 rounded-full flex items-center justify-center transition-all ${
                      isActive 
                        ? 'bg-[#F3F4F6] text-[#111214] shadow-md font-semibold' 
                        : 'text-[#727780] hover:text-[#F3F4F6] hover:bg-[#1D2024]'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </NavLink>

                  {/* Restrained tooltip */}
                  {hoveredItem === item.id && (
                    <div className="absolute left-[64px] top-1/2 -translate-y-1/2 flex items-center px-2.5 py-1 rounded bg-[#24272C] border border-[#30343A] text-[12px] font-medium text-[#F3F4F6] whitespace-nowrap shadow-xl z-50 pointer-events-none">
                      {item.label}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </div>

        {/* Bottom Rail Items */}
        <div className="flex flex-col items-center gap-2">
          {bottomNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <div 
                key={item.id} 
                className="relative"
                onMouseEnter={() => setHoveredItem(item.id)}
                onMouseLeave={() => setHoveredItem(null)}
              >
                <NavLink
                  to={item.path}
                  aria-label={item.label}
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                    isActive 
                      ? 'bg-[#24272C] text-[#D8E7A2] border border-[#3E4829]' 
                      : 'text-[#727780] hover:text-[#F3F4F6] hover:bg-[#1D2024]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </NavLink>

                {hoveredItem === item.id && (
                  <div className="absolute left-[64px] top-1/2 -translate-y-1/2 flex items-center px-2.5 py-1 rounded bg-[#24272C] border border-[#30343A] text-[12px] font-medium text-[#F3F4F6] whitespace-nowrap shadow-xl z-50 pointer-events-none">
                    {item.label}
                  </div>
                )}
              </div>
            );
          })}

          {/* Help trigger */}
          <div 
            className="relative"
            onMouseEnter={() => setHoveredItem('help')}
            onMouseLeave={() => setHoveredItem(null)}
          >
            <button
              onClick={() => setShowHelpModal(true)}
              aria-label="Documentation &amp; Shortcuts"
              className="w-10 h-10 rounded-full flex items-center justify-center text-[#727780] hover:text-[#F3F4F6] hover:bg-[#1D2024] transition-all"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
            {hoveredItem === 'help' && (
              <div className="absolute left-[64px] top-1/2 -translate-y-1/2 flex items-center px-2.5 py-1 rounded bg-[#24272C] border border-[#30343A] text-[12px] font-medium text-[#F3F4F6] whitespace-nowrap shadow-xl z-50 pointer-events-none">
                Help &amp; Shortcuts
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Help Modal */}
      {showHelpModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-lg rounded border border-[#30343A] bg-[#17191C] shadow-2xl p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-[#262A30] pb-3">
              <div className="flex items-center gap-2.5">
                <img src={logoImg} alt="Leddro Mark" className="w-6 h-6 rounded-md object-contain p-0.5 bg-[#111214] border border-[#2B2F36]" />
                <img src={nameLogoImg} alt="Leddro" className="h-4.5 w-auto object-contain" />
                <span className="text-[13px] font-medium text-[#A0A5AD]">• Shortcuts &amp; Principles</span>
              </div>
              <button onClick={() => setShowHelpModal(false)} className="text-[#727780] hover:text-[#F3F4F6]">
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="flex flex-col gap-2.5 text-[12px] text-[#A0A5AD]">
              <div className="flex items-center justify-between py-1 border-b border-[#22252B]">
                <span>Global Command Palette</span>
                <span className="font-mono bg-[#1D2024] px-2 py-0.5 rounded text-[#F3F4F6] border border-[#30343A]">Ctrl / Cmd + K</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-[#22252B]">
                <span>Run Diagnostic Audit</span>
                <span className="font-mono bg-[#1D2024] px-2 py-0.5 rounded text-[#F3F4F6] border border-[#30343A]">Click 'Run Audit'</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-[#22252B]">
                <span>Quick Row Navigation</span>
                <span className="font-mono bg-[#1D2024] px-2 py-0.5 rounded text-[#F3F4F6] border border-[#30343A]">Arrow Up / Down</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-[#22252B]">
                <span>Close Detail Inspector</span>
                <span className="font-mono bg-[#1D2024] px-2 py-0.5 rounded text-[#F3F4F6] border border-[#30343A]">Esc</span>
              </div>
            </div>

            <div className="rounded p-3 bg-[#111214] border border-[#262A30] text-[12px] text-[#727780] flex flex-col gap-1">
              <div className="font-medium text-[#A0A5AD]">Zero-hallucination policy</div>
              <div>Deterministic crawler observations are separated strictly from generative AI copy suggestions. Raw HTTP dumps and TLS traces are always available as inspectable proof.</div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowHelpModal(false)}
                className="px-3 py-1.5 rounded bg-[#1D2024] border border-[#30343A] text-[12px] text-[#F3F4F6] hover:bg-[#25282F]"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
