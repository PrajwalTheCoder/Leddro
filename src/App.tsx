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
