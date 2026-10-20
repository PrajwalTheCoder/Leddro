import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Play, 
  ExternalLink, 
  Sparkles, 
  ShieldCheck, 
  Search, 
  Cpu, 
  Send, 
  Activity, 
  CheckCircle2, 
  Radar, 
  Network, 
  ArrowRight, 
  ChevronDown,
  Terminal,
  Lock,
  Globe,
  Layers,
  FileCheck2,
  AlertTriangle
} from 'lucide-react';
import logoImg from '../assets/logo.png';
import nameLogoImg from '../assets/leddro-name-logo.png';

const GithubIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
  </svg>
);

interface LandingProps {
  youtubeUrl?: string;
}

export const Landing: React.FC<LandingProps> = ({ youtubeUrl = '' }) => {
  const navigate = useNavigate();
  const [activeVideoTab, setActiveVideoTab] = useState<number>(1);
  const [testUrl, setTestUrl] = useState('');
  const [ytLink, setYtLink] = useState(youtubeUrl);
  const [showYtModal, setShowYtModal] = useState(false);

  const videoTabs = [
    {
      id: 1,
      title: 'End-to-End Outreach Walkthrough',
      desc: 'Autonomous discovery, real-time DNS & TLS diagnostic probes, Cloudflare email XOR bypass, and evidence-backed draft synthesis.',
      duration: '3:45',
      badge: 'Full Pipeline'
    },
    {
      id: 2,
      title: 'Topological Relationship Graph',
      desc: 'Interactive D3 physics simulation mapping live telemetry links across prospects, nameservers, AI engines, and audit findings.',
      duration: '2:15',
      badge: 'Force Physics'
    },
    {
      id: 3,
      title: 'Zero-Hallucination AI Studio',
      desc: 'Strict claim-to-finding verification engine ensuring 0% hallucination rate with free-tier Gemini and local Ollama.',
      duration: '2:30',
      badge: 'AI Evidence'
    }
  ];

  const pipelineSteps = [
    {
      step: '01',
      title: 'Autonomous Discovery',
      icon: Search,
      desc: 'Multi-provider ingestion via OpenStreetMap Overpass API, local business registries, and high-speed CSV bulk imports with intra-batch deduplication.',
      tags: ['OSM Overpass', 'CSV Ingestion', 'Deduplication']
    },
    {
      step: '02',
      title: 'Deep Website Diagnostics',
      icon: ShieldCheck,
      desc: 'Zero-credential multi-point probes inspecting authoritative DNS zone records (A, MX, SPF, DMARC), TLS handshake ciphers, and mobile viewports.',
      tags: ['DNS Zone Probe', 'TLS Ciphers', 'SSRF Guard']
    },
    {
      step: '03',
      title: 'Contact & Cloudflare Bypass',
      icon: Lock,
      desc: 'DOM regex extraction with client-side XOR decryption for Cloudflare email protection (<span data-cfemail>) and obfuscated mailto tags.',
      tags: ['Cloudflare XOR', 'DOM Traversal', 'MX Validation']
    },
    {
      step: '04',
      title: 'Evidence-Grounded AI Generation',
      icon: Cpu,
      desc: 'Strict Claim-to-Finding citation mapping ensuring every factual assertion references a verified diagnostic finding ID with zero hallucinations.',
      tags: ['Gemini Free Tier', 'Claim Mapping', '0% Hallucination']
    },
    {
      step: '05',
      title: 'Supervised Dispatch Control',
      icon: Send,
      desc: 'Strictly single-message human-approved sending through Google OAuth Gmail Gateway or direct SMTP. No unreviewed blasts or auto-dialers.',
      tags: ['Google OAuth', 'Direct SMTP', 'Human-in-the-Loop']
    }
  ];

  const scenarios = [
    {
      tag: 'WEB DEVELOPMENT / AGENCIES',
      title: 'Mobile & Performance Revamps',
      desc: 'Instantly pinpoint prospects with missing mobile viewports, unminified CSS, broken SSL, or HTTP redirects to pitch high-converting website redesigns.'
    },
    {
      tag: 'CYBERSECURITY / IT ADVISORY',
      title: 'TLS & DNS Vulnerability Audits',
      desc: 'Flag impending SSL certificate expirations, deprecated TLS 1.0/1.1 protocols, missing HSTS headers, and open email relays.'
    },
    {
      tag: 'EMAIL DELIVERABILITY',
      title: 'SPF & DMARC Mandate Compliance',
      desc: 'Detect missing anti-spoofing policies to help clients pass modern Google and Yahoo recipient inbox authentication standards.'
    },
    {
      tag: 'LOCAL B2B CONSULTANTS',
      title: 'Opportunity-Scored Acquisition',
      desc: 'Discover clinics, legal practices, and regional businesses ranked by commercial intent, technical urgency, and resolution ease.'
    },
    {
      tag: 'SEO & DIGITAL STRATEGY',
      title: 'Core Web Vitals & TTFB Diagnostics',
      desc: 'Measure initial server response lag, missing canonical tags, and page size bloat with timestamped proof for pitch decks.'
    },
    {
      tag: 'LEGAL & HEALTHCARE COMPLIANCE',
      title: 'Client Intake Privacy Audits',
      desc: 'Ensure medical practices and law firms maintain encrypted HTTPS form submissions and confidential patient communication channels.'
    }
  ];

  const handleQuickAudit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/app');
  };

  return (
    <div className="w-full min-h-screen bg-[#0A0D13] text-[#F3F4F6] font-sans selection:bg-[#D2F824] selection:text-black overflow-x-hidden">
      {/* GLOW BACKGROUND ACCENTS */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-to-b from-[#D2F824]/10 via-[#2753FF]/5 to-transparent blur-[140px] opacity-70" />
        <div className="absolute top-[40%] -left-40 w-[600px] h-[600px] bg-[#2753FF]/10 blur-[160px] opacity-40" />
        <div className="absolute top-[70%] -right-40 w-[600px] h-[600px] bg-[#D2F824]/10 blur-[160px] opacity-30" />
        <div className="absolute inset-0 bg-[radial-gradient(#1E2330_1px,transparent_1px)] [background-size:24px_24px] opacity-30" />
      </div>

      {/* TOP HEADER / NAVBAR */}
      <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-[#0A0D13]/80 border-b border-[#1E2330]">
        <div className="w-full max-w-7xl mx-auto px-6 h-18 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3.5 group">
            <div className="w-11 h-11 rounded-xl bg-[#111214] border border-[#2B303C] flex items-center justify-center p-1.5 shadow-[0_0_15px_rgba(210,248,36,0.15)] group-hover:border-[#D2F824] transition-all">
              <img src={logoImg} alt="Leddro Mark" className="w-full h-full object-contain" />
            </div>
            <div className="flex flex-col justify-center">
              <div className="flex items-center gap-2.5">
                <img src={nameLogoImg} alt="Leddro" className="h-8 sm:h-9 w-auto object-contain" />
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1C202B] text-[#D2F824] border border-[#2B303C]">
                  v1.0 MIT
                </span>
              </div>
              <span className="text-[11px] text-[#8B949E] font-mono">Autonomous Diagnostic Outreach</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[#9BA1B0]">
            <a href="#workflow" className="hover:text-white transition-colors">Workflow</a>
            <a href="#video-tour" className="hover:text-white transition-colors">Demo Video</a>
            <a href="#scenarios" className="hover:text-white transition-colors">Scenarios</a>
            <a href="#architecture" className="hover:text-white transition-colors">Security</a>
            <a 
              href="https://github.com/PrajwalTheCoder/Leddro#table-of-contents" 
              target="_blank" 
              rel="noreferrer" 
              className="hover:text-white transition-colors"
            >
              Docs
            </a>
          </nav>

          {/* Right Action CTAs */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/PrajwalTheCoder/Leddro"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#141720] hover:bg-[#1E2330] border border-[#262B38] text-xs font-mono text-white transition-all hover:border-[#8B949E]"
            >
              <GithubIcon className="w-4 h-4 text-white" />
              <span>Star on GitHub</span>
            </a>
            <button
              onClick={() => navigate('/app')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#D2F824] hover:bg-[#c2e620] text-black font-semibold text-xs tracking-tight shadow-[0_0_20px_rgba(210,248,36,0.35)] transition-all hover:scale-[1.02] cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 fill-black" />
              <span>Try Live Demo</span>
            </button>
          </div>
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="relative z-10 pt-20 pb-24 px-6 text-center w-full max-w-5xl mx-auto">
        {/* Open Source Pill Badge */}
        <div className="inline-flex items-center gap-3 px-5 py-2 rounded-full bg-[#141822] border border-[#262B38] shadow-inner mb-8 animate-fade-in">
          <img src={logoImg} alt="Leddro Mark" className="w-5.5 h-5.5 object-contain" />
          <img src={nameLogoImg} alt="Leddro" className="h-5 sm:h-5.5 w-auto object-contain" />
          <span className="text-xs text-[#8B949E]">|</span>
          <span className="text-xs font-mono text-[#D2F824] font-medium">
            100% Free &amp; Open-Source (MIT)
          </span>
          <span className="text-xs text-[#8B949E]">|</span>
          <span className="text-xs text-[#9BA1B0] font-mono">
            Zero Hallucinations • Hardened SSRF Defenses
          </span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.08] mb-6">
          Outreach Grounded in <br className="hidden sm:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-[#E6EDF3] to-[#8B949E]">
            Verifiable Evidence.
          </span>
        </h1>

        {/* Hero Subtitle */}
        <p className="text-lg sm:text-xl text-[#9BA1B0] max-w-3xl mx-auto font-normal leading-relaxed mb-10">
          The autonomous discovery, deep website diagnostics, and evidence-grounded cold outreach engine.
          Automated multi-point website probes, client-side Cloudflare email decoding, and strictly human-supervised dispatch.
        </p>

        {/* Hero Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <button
            onClick={() => navigate('/app')}
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-xl bg-[#D2F824] hover:bg-[#c2e620] text-black font-bold text-sm tracking-tight shadow-[0_0_30px_rgba(210,248,36,0.35)] transition-all hover:scale-105 cursor-pointer"
          >
            <Sparkles className="w-4 h-4 fill-black" />
            <span>Launch Live Demo Sandbox</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <a
            href="https://github.com/PrajwalTheCoder/Leddro"
            target="_blank"
            rel="noreferrer"
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-xl bg-[#141822] hover:bg-[#1E2330] border border-[#2B303C] text-sm font-mono text-white transition-all hover:border-[#8B949E]"
          >
            <GithubIcon className="w-4 h-4 text-white" />
            <span>Star on GitHub</span>
          </a>
        </div>

        {/* Simulated Quick Launch Form */}
        <div className="max-w-xl mx-auto p-1.5 rounded-2xl bg-[#141720]/80 border border-[#262B38] shadow-2xl backdrop-blur-md">
          <form onSubmit={handleQuickAudit} className="flex items-center gap-2">
            <div className="flex items-center gap-2.5 pl-4 flex-1 text-[#8B949E]">
              <Globe className="w-4 h-4 text-[#D2F824]" />
              <input
                type="text"
                value={testUrl}
                onChange={(e) => setTestUrl(e.target.value)}
                placeholder="Enter domain to explore (e.g., example.com)"
                className="w-full bg-transparent text-sm text-white placeholder-[#586069] focus:outline-none font-mono"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-[#1E2330] hover:bg-[#272D3D] text-white text-xs font-mono font-medium transition-colors border border-[#303644] cursor-pointer"
            >
              Simulate Audit
            </button>
          </form>
        </div>

        {/* Scroll Cue */}
        <div className="mt-14 flex flex-col items-center gap-2 text-xs font-mono text-[#586069]">
          <span>EXPLORE ARCHITECTURE & WALKTHROUGH</span>
          <ChevronDown className="w-4 h-4 animate-bounce text-[#D2F824]" />
        </div>
      </section>

      {/* DEMO VIDEO SHOWCASE SECTION (MiroFish Style) */}
      <section id="video-tour" className="relative z-10 py-20 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <span className="text-xs font-mono tracking-widest text-[#D2F824] uppercase font-bold">
            DEMO VIDEOS & WALKTHROUGH
          </span>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white mt-3 flex items-center justify-center gap-3 sm:gap-4.5 flex-wrap">
            <span>Watch</span>
            <img src={nameLogoImg} alt="Leddro" className="h-9 sm:h-12 md:h-14 w-auto object-contain inline-block drop-shadow-[0_0_25px_rgba(210,248,36,0.25)]" />
            <span>in Action</span>
          </h2>
          <p className="text-sm text-[#8B949E] max-w-2xl mx-auto mt-3">
            See how <img src={nameLogoImg} alt="Leddro" className="h-4 sm:h-4.5 w-auto object-contain inline-block align-middle mx-1.5 -mt-0.5" /> extracts technical website defects, maps relationship graphs, and compiles evidence-based cold emails with zero hallucinations.
          </p>
        </div>

        {/* Video Player + Playlist Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Playlist Tabs */}
          <div className="lg:col-span-4 flex flex-col gap-4">
            {videoTabs.map((tab) => {
              const isActive = activeVideoTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveVideoTab(tab.id)}
                  className={`text-left p-5 rounded-2xl border transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#141822] border-[#D2F824]/60 shadow-[0_0_20px_rgba(210,248,36,0.1)]'
                      : 'bg-[#10131A] border-[#1E2330] hover:bg-[#141822] hover:border-[#2B303C]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-[#8B949E]">0{tab.id} / CHAPTER</span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                      isActive ? 'bg-[#D2F824] text-black font-bold' : 'bg-[#1C202B] text-[#8B949E]'
                    }`}>
                      {tab.badge}
                    </span>
                  </div>
                  <h3 className={`text-base font-bold mb-1 ${isActive ? 'text-white' : 'text-[#C9D1D9]'}`}>
                    {tab.title}
                  </h3>
                  <p className="text-xs text-[#8B949E] leading-relaxed">
                    {tab.desc}
                  </p>
                </button>
              );
            })}

            {/* Quick config button for YouTube link */}
            <button
              onClick={() => setShowYtModal(true)}
              className="mt-2 text-xs font-mono text-[#8B949E] hover:text-[#D2F824] flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <span>⚙ Set YouTube Embed URL</span>
            </button>
          </div>

          {/* Right Video Screen Viewport */}
          <div className="lg:col-span-8">
            <div className="relative aspect-video rounded-3xl bg-[#0F131C] border border-[#232836] shadow-2xl overflow-hidden group flex flex-col items-center justify-center">
              {ytLink ? (
                <iframe
                  src={ytLink.includes('embed') ? ytLink : `https://www.youtube.com/embed/${ytLink.split('v=')[1] || ytLink.split('/').pop()}`}
                  title="Leddro Walkthrough Video"
                  className="w-full h-full border-0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              ) : (
                /* Video Player Placeholder with High-Tech Aesthetics */
                <div className="relative w-full h-full flex flex-col items-center justify-center p-8 select-none">
                  {/* Glowing Radar backdrop inside screen */}
                  <div className="absolute inset-0 bg-gradient-to-tr from-[#0F131C] via-[#141B2B] to-[#0A0D13] opacity-90" />
                  <div className="absolute inset-0 bg-[radial-gradient(#2753FF_1px,transparent_1px)] [background-size:20px_20px] opacity-20" />
                  
                  {/* Decorative Scanlines */}
                  <div className="absolute top-4 left-6 right-6 flex items-center justify-between text-[11px] font-mono text-[#8B949E] z-10">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#D2F824] animate-pulse" />
                      <span className="text-white font-medium">STREAM: LEDDRO_WALKTHROUGH_1080P</span>
                    </div>
                    <span>CH: 0{activeVideoTab} • 60 FPS • D3 PHYSICS ACTIVE</span>
                  </div>

                  {/* Play Button Icon */}
                  <div 
                    onClick={() => navigate('/app')}
                    className="relative z-10 w-20 h-20 rounded-full bg-[#1C2232] border border-[#D2F824]/40 flex items-center justify-center cursor-pointer shadow-[0_0_35px_rgba(210,248,36,0.25)] group-hover:scale-110 group-hover:border-[#D2F824] transition-all"
                  >
                    <Play className="w-8 h-8 fill-[#D2F824] text-[#D2F824] ml-1" />
                  </div>

                  <div className="relative z-10 text-center mt-6">
                    <span className="text-xs font-mono uppercase tracking-wider text-[#D2F824]">
                      {videoTabs[activeVideoTab - 1].title}
                    </span>
                    <p className="text-sm text-white font-medium mt-1">
                      Click to Launch Interactive In-Browser Demo
                    </p>
                    <span className="text-[11px] text-[#8B949E] font-mono mt-0.5 block">
                      (YouTube video link ready for configuration)
                    </span>
                  </div>

                  <div className="absolute bottom-4 left-6 right-6 flex items-center justify-between text-[10px] font-mono text-[#586069] z-10">
                    <span>STATUS: 200 OK</span>
                    <span>MIT OPEN SOURCE</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 5-STEP PIPELINE SECTION (MiroFish Style) */}
      <section id="workflow" className="relative z-10 py-24 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <span className="text-xs font-mono tracking-widest text-[#D2F824] uppercase font-bold">
            ARCHITECTURE & EXECUTION
          </span>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white mt-2">
            Outreach Pipeline in 5 Steps
          </h2>
          <p className="text-sm text-[#8B949E] max-w-2xl mx-auto mt-3">
            Built for end-to-end automation, strict operator verification, and deterministic safety guardrails.
          </p>
        </div>

        {/* 5 Step Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {pipelineSteps.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="p-6 rounded-2xl bg-[#11141C] border border-[#1E2330] hover:border-[#D2F824]/50 transition-all hover:-translate-y-1 group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-mono font-bold text-[#D2F824]">
                      {item.step}
                    </span>
                    <div className="w-8 h-8 rounded-lg bg-[#181D28] flex items-center justify-center text-[#8B949E] group-hover:text-white transition-colors">
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <h3 className="text-base font-bold text-white mb-2 leading-snug">
                    {item.title}
                  </h3>
                  <p className="text-xs text-[#8B949E] leading-relaxed mb-4">
                    {item.desc}
                  </p>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-3 border-t border-[#1C202B]">
                  {item.tags.map((tag) => (
                    <span key={tag} className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#161A24] text-[#9BA1B0]">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* BUILT FOR EVERY SCENARIO GRID (MiroFish Style) */}
      <section id="scenarios" className="relative z-10 py-20 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <span className="text-xs font-mono tracking-widest text-[#D2F824] uppercase font-bold">
            USE CASES & VERTICALS
          </span>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white mt-2">
            Built for Every Scenario
          </h2>
          <p className="text-sm text-[#8B949E] max-w-2xl mx-auto mt-3">
            From solo freelance developers to enterprise cybersecurity consultancies, Leddro turns raw technical diagnostic audits into trusted client relationships.
          </p>
        </div>

        {/* 6 Scenario Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {scenarios.map((sc, i) => (
            <div
              key={i}
              className="p-7 rounded-2xl bg-[#11141C] border border-[#1E2330] hover:border-[#384054] transition-all hover:bg-[#141822]"
            >
              <span className="text-[10px] font-mono tracking-wider text-[#D2F824] font-semibold uppercase block mb-2">
                {sc.tag}
              </span>
              <h3 className="text-lg font-bold text-white mb-2">
                {sc.title}
              </h3>
              <p className="text-xs text-[#8B949E] leading-relaxed">
                {sc.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* BOTTOM CTA / LAUNCH BANNER */}
      <section className="relative z-10 py-24 px-6 max-w-5xl mx-auto text-center">
        <div className="p-10 sm:p-16 rounded-3xl bg-gradient-to-b from-[#141824] to-[#0E1118] border border-[#272E3E] shadow-2xl relative overflow-hidden">
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[400px] h-[200px] bg-[#D2F824]/20 blur-[90px] pointer-events-none" />

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Experience the Live Interactive Sandbox
          </h2>
          <p className="text-sm text-[#9BA1B0] max-w-xl mx-auto mb-8 leading-relaxed">
            Test the full interface now. Explore the real-time Tactical Radar, drag nodes in the Relationship Graph, and inspect evidence-based AI drafts with simulated mock data.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/app')}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-[#D2F824] hover:bg-[#c2e620] text-black font-bold text-sm tracking-tight shadow-[0_0_25px_rgba(210,248,36,0.35)] transition-all cursor-pointer hover:scale-105"
            >
              <Sparkles className="w-4 h-4 fill-black" />
              <span>Launch Live Demo Sandbox</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <a
              href="https://github.com/PrajwalTheCoder/Leddro"
              target="_blank"
              rel="noreferrer"
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-[#1A1F2B] hover:bg-[#23293A] border border-[#2B3242] text-sm font-mono text-white transition-colors"
            >
              <GithubIcon className="w-4 h-4" />
              <span>View Source on GitHub</span>
            </a>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="relative z-10 border-t border-[#1C202B] py-10 px-6 text-center text-xs text-[#8B949E] font-mono">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <img src={logoImg} alt="Leddro Logo" className="w-5 h-5 object-contain" />
            <img src={nameLogoImg} alt="Leddro" className="h-4 w-auto object-contain" />
            <span className="text-white font-medium">• Intelligence</span>
            <span>•</span>
            <span>MIT Open Source License</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/app" className="text-white hover:text-[#D2F824] transition-colors">Interactive Sandbox</Link>
            <a href="https://github.com/PrajwalTheCoder/Leddro" target="_blank" rel="noreferrer" className="text-white hover:text-[#D2F824] transition-colors">GitHub Repository</a>
          </div>
        </div>
      </footer>

      {/* YOUTUBE LINK CONFIG MODAL */}
      {showYtModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#141822] border border-[#2B3242] p-6 rounded-2xl max-w-md w-full shadow-2xl">
            <h3 className="text-base font-bold text-white mb-2">Configure YouTube Video Link</h3>
            <p className="text-xs text-[#8B949E] mb-4">
              Paste your YouTube video URL or ID (e.g. <code>https://www.youtube.com/watch?v=XXXX</code> or <code>https://youtu.be/XXXX</code>).
            </p>
            <input
              type="text"
              value={ytLink}
              onChange={(e) => setYtLink(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full px-3 py-2 rounded-xl bg-[#0F1218] border border-[#262B38] text-sm text-white focus:outline-none focus:border-[#D2F824] font-mono mb-4"
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowYtModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-mono text-[#8B949E] hover:text-white"
              >
                Close
              </button>
              <button
                onClick={() => setShowYtModal(false)}
                className="px-4 py-2 rounded-xl bg-[#D2F824] text-black font-bold text-xs font-mono"
              >
                Save Video
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
