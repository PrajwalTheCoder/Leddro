import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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
import { useApp } from './context/AppContext';

const BackendStatusBanner: React.FC = () => {
  const { backendOnline, checkBackendHealth } = useApp();
  const [isRetrying, setIsRetrying] = React.useState(false);

  if (backendOnline !== false) return null;

  const handleRetry = async () => {
    setIsRetrying(true);
    await checkBackendHealth();
    setIsRetrying(false);
  };

  return (
    <div className="bg-[#2A1818] border-b border-[#4A2626] px-4 py-2 flex items-center justify-between text-xs text-[#D78383] shrink-0 z-10 transition-all">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[#D78383] animate-pulse shrink-0" />
        <span>
          <strong className="text-white font-medium">FastAPI Engine Offline:</strong> Web UI cannot reach <code className="bg-[#1C1010] px-1.5 py-0.5 rounded text-[#F3F4F6] font-mono text-[11px]">http://127.0.0.1:8000/api/health</code>. Live website audits, AI drafting, and database persistence require the backend engine.
        </span>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={handleRetry}
          disabled={isRetrying}
          className="px-2.5 py-1 rounded bg-[#3D2020] hover:bg-[#4D2828] text-white font-medium text-[11px] transition-colors cursor-pointer disabled:opacity-50"
        >
          {isRetrying ? 'Checking...' : 'Retry Connection'}
        </button>
        <a
          href="https://github.com/PrajwalTheCoder/Leddro#running-the-application"
          target="_blank"
          rel="noreferrer"
          className="underline text-[#F3F4F6] hover:text-white text-[11px]"
        >
          Setup Guide
        </a>
      </div>
    </div>
  );
};

export function App() {
  return (
    <AppProvider>
      <Router>
        <div className="flex h-screen w-screen overflow-hidden bg-[#111214] text-[#F3F4F6] font-sans antialiased">
          {/* Left Navigation Rail (~72px) */}
          <Sidebar />

          {/* Main Workspace Area */}
          <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
            {/* Top Bar */}
            <TopBar />

            {/* Offline Engine Warning Banner */}
            <BackendStatusBanner />

            {/* Viewport Router */}
            <main className="flex-1 overflow-hidden relative">
              <Routes>
                <Route path="/" element={<Overview />} />
                <Route path="/discover" element={<Discover />} />
                <Route path="/prospects" element={<Prospects />} />
                <Route path="/audits" element={<Audits />} />
                <Route path="/drafts" element={<Drafts />} />
                <Route path="/integrations" element={<Integrations />} />
                <Route path="/history" element={<History />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>

          {/* Global Overlays */}
          <CommandPalette />
          <ToastContainer />
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;
