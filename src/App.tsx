import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { Sidebar } from './components/navigation/Sidebar';
import { TopBar } from './components/navigation/TopBar';
import { CommandPalette } from './components/common/CommandPalette';
import { ToastContainer } from './components/common/ToastContainer';

// Pages
import { Overview } from './pages/Overview';
import { Discover } from './pages/Discover';
import { Prospects } from './pages/Prospects';
import { Audits } from './pages/Audits';
import { Drafts } from './pages/Drafts';
import { Integrations } from './pages/Integrations';
import { History } from './pages/History';
import { Landing } from './pages/Landing';
import { useApp } from './context/AppContext';

function AppContent() {
  const location = useLocation();
  const { backendOnline } = useApp();

  const isHostedDemo = typeof window !== 'undefined' && (
    window.location.hostname.includes('github.io') ||
    window.location.hostname.includes('vercel.app') ||
    window.location.hostname.includes('pages.dev')
  );

  // Landing showcase is ONLY shown:
  // 1) Explicitly visiting /landing
  // 2) On hosted demo site (GitHub Pages) when visiting root / with no backend
  const isLanding = location.pathname === '/landing' || (isHostedDemo && !backendOnline && (location.pathname === '/' || location.pathname === ''));

  if (isLanding) {
    return (
      <div className="w-full min-h-screen overflow-x-hidden bg-[#0A0D13]">
        <Landing />
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#111214] text-[#F3F4F6] font-sans antialiased">
      {/* Left Navigation Rail (~72px) */}
      <Sidebar />

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        {/* Top Bar */}
        <TopBar />

        {/* Viewport Router */}
        <main className="flex-1 overflow-hidden relative">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/app" element={<Overview />} />
            <Route path="/discover" element={<Discover />} />
            <Route path="/prospects" element={<Prospects />} />
            <Route path="/audits" element={<Audits />} />
            <Route path="/drafts" element={<Drafts />} />
            <Route path="/integrations" element={!isHostedDemo || backendOnline ? <Integrations /> : <Navigate to="/" replace />} />
            <Route path="/history" element={<History />} />
            <Route path="/landing" element={<Landing />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>

      {/* Global Overlays */}
      <CommandPalette />
      <ToastContainer />
    </div>
  );
}

const getBasename = (): string => {
  if (typeof window !== 'undefined') {
    const segments = window.location.pathname.split('/').filter(Boolean);
    if (segments.length > 0 && segments[0].toLowerCase() === 'leddro') {
      return '/Leddro';
    }
  }
  return import.meta.env.BASE_URL || '/';
};

export function App() {
  return (
    <AppProvider>
      <Router basename={getBasename()}>
        <AppContent />
      </Router>
    </AppProvider>
  );
}

export default App;
