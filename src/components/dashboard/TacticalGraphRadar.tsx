import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  forceSimulation,
  forceCenter,
  forceManyBody,
  forceCollide,
  forceLink,
  forceRadial,
  Simulation,
  SimulationNodeDatum,
  SimulationLinkDatum
} from 'd3-force';
import {
  Radio,
  RotateCcw,
  Maximize2,
  Plus,
  Minus,
  Layers,
  Activity,
  Mail,
  Building2,
  Play,
  Check,
  CheckCircle2,
  AlertTriangle,
  X,
  Timer,
  Radar as RadarIcon,
  Network
} from 'lucide-react';
import { Prospect } from '../../types';

export interface SimNode extends SimulationNodeDatum {
  id: string;
  name: string;
  label: string;
  subLabel?: string;
  category: 'hub' | 'prospect' | 'ai_engine' | 'gateway' | 'database' | 'finding';
  colorType: 'lime' | 'rose' | 'amber' | 'emerald' | 'blue' | 'purple' | 'orange' | 'cyan';
  radius: number;
  prospectId?: string;
  status?: string;
  opportunityScore?: number;
  websiteStatus?: string;
  orbitRadius?: number;
  websiteUrl?: string;
}

export interface SimLink extends SimulationLinkDatum<SimNode> {
  id: string;
  source: string | SimNode;
  target: string | SimNode;
  label?: string;
  color?: string;
  dash?: string;
  distance?: number;
  strength?: number;
}

interface TacticalGraphRadarProps {
  prospects: Prospect[];
  activeTarget?: Prospect;
  onSelectProspect: (id: string) => void;
  onRunAudit: (id: string, e?: React.MouseEvent) => Promise<void>;
  onCreateDraft: (id: string, e?: React.MouseEvent) => void;
  isAuditing: boolean;
  auditingProspectId: string | null;
  googleStatus?: { is_connected: boolean; email?: string | null } | null;
  liveRadar: boolean;
  showInspectorCard: boolean;
  setShowInspectorCard: (show: boolean) => void;
}

export const TacticalGraphRadar: React.FC<TacticalGraphRadarProps> = ({
  prospects,
  activeTarget,
  onSelectProspect,
  onRunAudit,
  onCreateDraft,
  isAuditing,
  auditingProspectId,
  googleStatus,
  liveRadar,
  showInspectorCard,
  setShowInspectorCard
}) => {
  // Mode: 'radar' for tactical HUD with compass & orbits, 'graph' for MiroFish relationship view
  const [viewMode, setViewMode] = useState<'radar' | 'graph'>('radar');
  const [showEdgeLabels, setShowEdgeLabels] = useState(true);
  const [radarZoom, setRadarZoom] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [, setTick] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<Simulation<SimNode, SimLink> | null>(null);
  const nodeCacheRef = useRef<Map<string, { x: number; y: number; vx?: number; vy?: number }>>(new Map());
  const dragRef = useRef<{
    node: SimNode;
    startX: number;
    startY: number;
    moved: boolean;
  } | null>(null);
  const panStartRef = useRef<{ x: number; y: number; panX: number; panY: number }>({
    x: 0,
    y: 0,
    panX: 0,
    panY: 0
  });

  const [dimensions, setDimensions] = useState({ width: 1100, height: 480 });

  // Track container size
  useEffect(() => {
    if (!containerRef.current) return;
    const updateDims = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setDimensions({
          width: clientWidth || 1100,
          height: clientHeight || 480
        });
      }
    };
    updateDims();
    const observer = new ResizeObserver(updateDims);
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Construct Graph Nodes and Links according to viewMode & data
  const { nodes, links } = useMemo(() => {
    const nList: SimNode[] = [];
    const lList: SimLink[] = [];

    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    // 1. Operator / Central Hub Node ("YOU / Leddro Hub")
    const hubId = 'hub_operator';
    nList.push({
      id: hubId,
      name: 'YOU (Leddro Hub)',
      label: googleStatus?.is_connected && googleStatus.email ? googleStatus.email : 'YOU (Leddro Hub)',
      subLabel: 'Command Engine',
      category: 'hub',
      colorType: 'emerald',
      radius: 20,
      orbitRadius: 0,
      x: centerX,
      y: centerY
    });

    if (viewMode === 'graph') {
      // MiroFish Mode: Add Infrastructure, AI Providers & Gateways
      nList.push({
        id: 'ai_gemini',
        name: 'Google Gemini',
        label: 'Google Gemini',
        subLabel: 'Draft Engine',
        category: 'ai_engine',
        colorType: 'blue',
        radius: 15,
        x: centerX - 160,
        y: centerY - 90
      });
      lList.push({
        id: 'link_hub_gemini',
        source: hubId,
        target: 'ai_gemini',
        label: 'GENERATES_WITH',
        color: '#3B82F6',
        distance: 140
      });

      nList.push({
        id: 'ai_openai',
        name: 'OpenAI GPT-4o',
        label: 'OpenAI',
        subLabel: 'Compatible Engine',
        category: 'ai_engine',
        colorType: 'blue',
        radius: 14,
        x: centerX - 210,
        y: centerY + 20
      });
      lList.push({
        id: 'link_hub_openai',
        source: hubId,
        target: 'ai_openai',
        label: 'SUPPORTS',
        color: '#60A5FA',
        dash: '4,4',
        distance: 160
      });

      nList.push({
        id: 'ai_claude',
        name: 'Claude 3.5',
        label: 'Claude',
        subLabel: 'Reasoning Engine',
        category: 'ai_engine',
        colorType: 'blue',
        radius: 14,
        x: centerX - 120,
        y: centerY - 170
      });
      lList.push({
        id: 'link_hub_claude',
        source: hubId,
        target: 'ai_claude',
        label: 'SUPPORTS',
        color: '#60A5FA',
        dash: '4,4',
        distance: 150
      });

      nList.push({
        id: 'gw_smtp',
        name: 'Gmail SMTP',
        label: 'Gmail SMTP',
        subLabel: googleStatus?.is_connected ? 'Active Gateway' : 'Configured',
        category: 'gateway',
        colorType: 'cyan',
        radius: 15,
        x: centerX - 80,
        y: centerY + 140
      });
      lList.push({
        id: 'link_hub_smtp',
        source: hubId,
        target: 'gw_smtp',
        label: 'DISPATCHES_VIA',
        color: '#06B6D4',
        distance: 130
      });

      nList.push({
        id: 'db_sqlite',
        name: 'leddro.db',
        label: 'SQLite Storage',
        subLabel: 'Local DB',
        category: 'database',
        colorType: 'purple',
        radius: 13,
        x: centerX + 70,
        y: centerY + 160
      });
      lList.push({
        id: 'link_hub_db',
        source: hubId,
        target: 'db_sqlite',
        label: 'STORES_IN',
        color: '#A855F7',
        distance: 140
      });
    }

    // 2. Prospects (Client Target Nodes)
    // In Radar mode, show up to 10 prominent prospects to keep tactical HUD clean; in Graph mode show up to 18
    const displayProspects = prospects.slice(0, viewMode === 'graph' ? 18 : 10);

    displayProspects.forEach((p, idx) => {
      const isSelected = activeTarget?.id === p.id;
      let colorType: SimNode['colorType'] = 'lime';
      if (p.status === 'contacted') {
        colorType = 'emerald';
      } else if (p.websiteStatus === 'ssl_expired' || p.websiteStatus === 'unreachable') {
        colorType = 'rose';
      } else if (p.websiteStatus === 'broken_pages' || p.status === 'needs_review') {
        colorType = 'amber';
      } else if (viewMode === 'graph') {
        colorType = 'orange'; // MiroFish entity aesthetic
      }

      // Assign tactical radar orbit radius based on opportunity & status
      let orbitRadius = 180;
      if (p.opportunityScore >= 85) orbitRadius = 130;
      else if (p.opportunityScore >= 60) orbitRadius = 210;
      else orbitRadius = 280;

      // Initial angle placement to avoid all starting at same position
      const angle = (idx / displayProspects.length) * 2 * Math.PI - Math.PI / 4;
      const initialX = centerX + Math.cos(angle) * (viewMode === 'radar' ? orbitRadius : 160 + (idx % 3) * 40);
      const initialY = centerY + Math.sin(angle) * (viewMode === 'radar' ? orbitRadius : 140 + (idx % 2) * 50);

      nList.push({
        id: `prospect_${p.id}`,
        prospectId: p.id,
        name: p.name,
        label: p.name,
        subLabel: p.location.city,
        category: 'prospect',
        colorType,
        radius: isSelected ? 17 : p.status === 'contacted' ? 14 : 12,
        opportunityScore: p.opportunityScore,
        websiteStatus: p.websiteStatus,
        status: p.status,
        orbitRadius,
        websiteUrl: p.websiteUrl,
        x: initialX,
        y: initialY
      });

      // Semantic link to Hub
      let linkRelation = 'AUDITED_BY';
      let strokeColor = '#262D3D';
      let dashPattern: string | undefined = '2,3';

      if (p.status === 'contacted') {
        linkRelation = 'CONNECTED_VIA_GMAIL';
        strokeColor = '#10B981';
        dashPattern = '5,5';
      } else if (p.status === 'draft_ready') {
        linkRelation = 'DRAFT_READY';
        strokeColor = '#F59E0B';
        dashPattern = '4,4';
      } else if (isSelected) {
        linkRelation = 'ACTIVE_TARGET';
        strokeColor = '#D2F824';
        dashPattern = undefined;
      } else if (p.websiteStatus === 'broken_pages') {
        linkRelation = 'HAS_404_ROUTE';
        strokeColor = '#F43F5E';
      } else if (p.websiteStatus === 'ssl_expired') {
        linkRelation = 'TLS_EXPIRED';
        strokeColor = '#F43F5E';
      }

      lList.push({
        id: `link_hub_${p.id}`,
        source: hubId,
        target: `prospect_${p.id}`,
        label: linkRelation,
        color: strokeColor,
        dash: dashPattern,
        distance: viewMode === 'radar' ? orbitRadius : 180
      });

      // In Graph mode, add cross-links for realism like MiroFish
      if (viewMode === 'graph' && p.status === 'contacted') {
        lList.push({
          id: `link_smtp_${p.id}`,
          source: 'gw_smtp',
          target: `prospect_${p.id}`,
          label: 'DISPATCHED_TO',
          color: '#10B981',
          dash: '4,4',
          distance: 140
        });
      }
    });

    return { nodes: nList, links: lList };
  }, [prospects, activeTarget, viewMode, googleStatus, dimensions]);

  // Run Butter-Smooth Physics Simulation with D3-Force
  useEffect(() => {
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    // Restore cached positions so nodes do not violently reset or jump
    nodes.forEach((n) => {
      const cached = nodeCacheRef.current.get(n.id);
      if (cached) {
        n.x = cached.x;
        n.y = cached.y;
        n.vx = cached.vx;
        n.vy = cached.vy;
      }
    });

    // Destroy old simulation
    if (simulationRef.current) {
      simulationRef.current.stop();
    }

    const sim = forceSimulation<SimNode>(nodes)
      .alphaDecay(0.022) // Slower damping for smooth liquid settling
      .velocityDecay(0.35); // Viscous fluid feel

    if (viewMode === 'radar') {
      // Tactical Radar Physics: Central anchor with radial rings + repulsion + collision
      sim
        .force('center', forceCenter(centerX, centerY).strength(0.06))
        .force('charge', forceManyBody<SimNode>().strength(-260))
        .force('collide', forceCollide<SimNode>().radius((d) => d.radius + 18).iterations(2))
        .force(
          'radial',
          forceRadial<SimNode>((d) => d.orbitRadius ?? 160, centerX, centerY).strength(0.4)
        )
        .force(
          'link',
          forceLink<SimNode, SimLink>(links)
            .id((d) => d.id)
            .distance((d) => d.distance ?? 160)
            .strength(0.35)
        );
    } else {
      // MiroFish Knowledge Graph Physics: Organic spring network with rich edge forces
      sim
        .force('center', forceCenter(centerX, centerY).strength(0.04))
        .force('charge', forceManyBody<SimNode>().strength(-340))
        .force('collide', forceCollide<SimNode>().radius((d) => d.radius + 22).iterations(2))
        .force(
          'link',
          forceLink<SimNode, SimLink>(links)
            .id((d) => d.id)
            .distance((d) => d.distance ?? 130)
            .strength(0.6)
        );
    }

    // Tick handler: smoothly store positions and trigger render
    sim.on('tick', () => {
      nodes.forEach((n) => {
        if (n.x !== undefined && n.y !== undefined) {
          nodeCacheRef.current.set(n.id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy });
        }
      });
      setTick((t) => (t + 1) % 1000000);
    });

    // Reheat simulation
    sim.alpha(0.6).restart();
    simulationRef.current = sim;

    return () => {
      sim.stop();
    };
  }, [nodes, links, viewMode, dimensions]);

  // Refresh physics layout (reheats the simulation like MiroFish refresh)
  const handleRefreshPhysics = () => {
    setIsRefreshing(true);
    if (simulationRef.current) {
      simulationRef.current.alpha(1).restart();
    }
    setTimeout(() => setIsRefreshing(false), 900);
  };

  // Dragging a specific Node with real spring elasticity
  const handleNodeMouseDown = (e: React.MouseEvent, node: SimNode) => {
    e.stopPropagation();
    if (!svgRef.current) return;

    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    const worldX = (clientX - panOffset.x) / radarZoom;
    const worldY = (clientY - panOffset.y) / radarZoom;

    dragRef.current = {
      node,
      startX: e.clientX,
      startY: e.clientY,
      moved: false
    };

    node.fx = worldX;
    node.fy = worldY;

    if (simulationRef.current) {
      simulationRef.current.alphaTarget(0.3).restart();
    }
  };

  // Canvas Mouse Down: Panning the background
  const handleBackgroundMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsPanning(true);
    panStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      panX: panOffset.x,
      panY: panOffset.y
    };
  };

  // Global Mouse Move: Handle either Node Dragging or Canvas Panning
  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      // 1. Moving a Node
      if (dragRef.current && svgRef.current) {
        const dist = Math.hypot(e.clientX - dragRef.current.startX, e.clientY - dragRef.current.startY);
        if (dist > 4) {
          dragRef.current.moved = true;
        }
        const rect = svgRef.current.getBoundingClientRect();
        const clientX = e.clientX - rect.left;
        const clientY = e.clientY - rect.top;
        const worldX = (clientX - panOffset.x) / radarZoom;
        const worldY = (clientY - panOffset.y) / radarZoom;

        dragRef.current.node.fx = worldX;
        dragRef.current.node.fy = worldY;
        return;
      }

      // 2. Panning Background
      if (isPanning) {
        const dx = e.clientX - panStartRef.current.x;
        const dy = e.clientY - panStartRef.current.y;
        setPanOffset({
          x: panStartRef.current.panX + dx,
          y: panStartRef.current.panY + dy
        });
      }
    },
    [isPanning, panOffset, radarZoom]
  );

  // Global Mouse Up: Release node or stop panning
  const handleMouseUp = useCallback(() => {
    if (dragRef.current) {
      const { node, moved } = dragRef.current;
      // If user barely moved the cursor, treat as a click to select prospect!
      if (!moved && node.prospectId) {
        onSelectProspect(node.prospectId);
        setShowInspectorCard(true);
      }
      // Release pin to allow smooth settling with physics
      node.fx = null;
      node.fy = null;
      if (simulationRef.current) {
        simulationRef.current.alphaTarget(0);
      }
      dragRef.current = null;
    }
    setIsPanning(false);
  }, [onSelectProspect, setShowInspectorCard]);

  // Mouse wheel zoom
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const zoomDelta = e.deltaY < 0 ? 0.08 : -0.08;
      setRadarZoom((prev) => {
        const next = Math.round((prev + zoomDelta) * 100) / 100;
        return Math.min(Math.max(next, 0.5), 2.4);
      });
    };

    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => el.removeEventListener('wheel', handleWheel);
  }, []);

  const handleResetView = () => {
    setRadarZoom(1);
    setPanOffset({ x: 0, y: 0 });
  };

  const centerX = dimensions.width / 2;
  const centerY = dimensions.height / 2;

  return (
    <div
      ref={containerRef}
      onMouseDown={handleBackgroundMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      className={`relative w-full h-[450px] lg:h-[490px] overflow-hidden select-none transition-colors border border-[#262D3D] rounded-2xl ${
        viewMode === 'graph' ? 'mirofish-dots' : 'bg-[#0A0D13] tactical-grid'
      } ${isPanning ? 'cursor-grabbing' : 'cursor-grab'}`}
    >
      {/* TOP HEADER CONTROLS (MiroFish Style Toolbar) */}
      <div
        onMouseDown={(e) => e.stopPropagation()}
        className="absolute top-3 inset-x-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-auto"
      >
        {/* Left: View Mode Switcher Pills & Title */}
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-[#161A23]/95 border border-[#262D3D] rounded-xl p-1 shadow-lg backdrop-blur-md">
            <button
              onClick={() => setViewMode('radar')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-mono font-medium transition-all ${
                viewMode === 'radar'
                  ? 'bg-[#D2F824] text-black shadow-[0_0_10px_rgba(210,248,36,0.25)] font-bold'
                  : 'text-[#8B949E] hover:text-white'
              }`}
            >
              <RadarIcon className="w-3.5 h-3.5" />
              <span>Tactical Radar</span>
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-mono font-medium transition-all ${
                viewMode === 'graph'
                  ? 'bg-[#D2F824] text-black shadow-[0_0_10px_rgba(210,248,36,0.25)] font-bold'
                  : 'text-[#8B949E] hover:text-white'
              }`}
            >
              <Network className="w-3.5 h-3.5" />
              <span>Relationship Graph</span>
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-[#8B949E]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D2F824] animate-pulse"></span>
            <span className="text-white font-medium">
              {viewMode === 'graph' ? 'Graph Relationship Visualization' : 'Tactical Radar Matrix'}
            </span>
          </div>
        </div>

        {/* Right: MiroFish Action Controls (Edge Labels, Refresh, Reset) */}
        <div className="flex items-center gap-2.5">
          {/* Toggle Edge Labels (MiroFish style purple switch) */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-xl bg-[#161A23]/95 border border-[#262D3D] text-xs font-mono text-[#8B949E] shadow-md backdrop-blur-md">
            <span className="cursor-pointer hover:text-white transition-colors" onClick={() => setShowEdgeLabels(!showEdgeLabels)}>
              Show Edge Labels
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={showEdgeLabels}
              onClick={() => setShowEdgeLabels(!showEdgeLabels)}
              className={`relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out focus:outline-none ${
                showEdgeLabels ? 'bg-[#7C3AED]' : 'bg-[#232938]'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-3 w-3 transform rounded-full shadow transition duration-200 ease-in-out mt-[2px] ${
                  showEdgeLabels ? 'translate-x-[14px] bg-white' : 'translate-x-[2px] bg-gray-400'
                }`}
              />
            </button>
          </div>

          {/* Refresh Physics Button (Reheats simulation) */}
          <button
            onClick={handleRefreshPhysics}
            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-[#161A23]/95 border border-[#262D3D] text-xs font-mono text-[#8B949E] hover:text-[#D2F824] hover:border-[#D2F824]/40 transition-colors shadow-md backdrop-blur-md"
            title="Refresh and reheat physics simulation"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-[#D2F824]' : ''}`} />
            <span className="hidden md:inline">Refresh</span>
          </button>

          {/* Reset / Center View Button */}
          <button
            onClick={handleResetView}
            className="p-1.5 rounded-xl bg-[#161A23]/95 border border-[#262D3D] text-[#8B949E] hover:text-white hover:border-[#D2F824]/40 transition-colors shadow-md backdrop-blur-md"
            title="Reset View Zoom & Center"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* SVG WORLD LAYER (Panning & Zooming with 60 FPS D3 Physics) */}
      <svg
        ref={svgRef}
        className="absolute inset-0 w-full h-full"
        style={{ overflow: 'hidden' }}
      >
        <defs>
          <filter id="glow-lime" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-emerald" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-purple" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <g
          transform={`translate(${panOffset.x}, ${panOffset.y}) scale(${radarZoom})`}
          style={{ transformOrigin: `${centerX}px ${centerY}px` }}
        >
          {/* RADAR MODE ONLY: Tactical Concentric Range Rings & Sweep Beam */}
          {viewMode === 'radar' && (
            <g className="pointer-events-none">
              <circle cx={centerX} cy={centerY} r={130} fill="none" stroke="#D2F824" strokeWidth="1" strokeOpacity="0.12" />
              <circle cx={centerX} cy={centerY} r={210} fill="none" stroke="#D2F824" strokeWidth="1" strokeOpacity="0.08" />
              <circle cx={centerX} cy={centerY} r={290} fill="none" stroke="#D2F824" strokeWidth="1" strokeOpacity="0.05" />
              <line x1={centerX - 310} y1={centerY} x2={centerX + 310} y2={centerY} stroke="#262D3D" strokeDasharray="3,3" strokeOpacity="0.4" />
              <line x1={centerX} y1={centerY - 310} x2={centerX} y2={centerY + 310} stroke="#262D3D" strokeDasharray="3,3" strokeOpacity="0.4" />
              {liveRadar && (
                <circle
                  cx={centerX}
                  cy={centerY}
                  r={290}
                  fill="url(#radar-gradient)"
                  className="animate-radar origin-center"
                  style={{ transformOrigin: `${centerX}px ${centerY}px` }}
                />
              )}
            </g>
          )}

          {/* DYNAMIC SPRING EDGES / VECTORS */}
          {links.map((link) => {
            const src = typeof link.source === 'object' ? link.source : nodes.find((n) => n.id === link.source);
            const tgt = typeof link.target === 'object' ? link.target : nodes.find((n) => n.id === link.target);

            if (!src || !tgt || src.x === undefined || src.y === undefined || tgt.x === undefined || tgt.y === undefined) {
              return null;
            }

            const isHovered = hoveredNodeId === src.id || hoveredNodeId === tgt.id;
            const isSelected = activeTarget && (src.prospectId === activeTarget.id || tgt.prospectId === activeTarget.id);

            const midX = (src.x + tgt.x) / 2;
            const midY = (src.y + tgt.y) / 2;

            const strokeColor = isSelected ? '#D2F824' : isHovered ? '#60A5FA' : link.color || '#262D3D';
            const strokeWidth = isSelected || isHovered ? 2.5 : 1.2;
            const strokeOpacity = isSelected || isHovered ? 0.95 : 0.45;

            return (
              <g key={link.id} className="pointer-events-none">
                {/* Glow layer when active */}
                {(isSelected || isHovered) && (
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke={strokeColor}
                    strokeWidth={5}
                    strokeOpacity={0.3}
                    filter="url(#glow-lime)"
                  />
                )}

                {/* Primary Spring Beam */}
                <line
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={link.dash}
                  strokeOpacity={strokeOpacity}
                />

                {/* MiroFish Edge Text Labels */}
                {showEdgeLabels && link.label && (
                  <g transform={`translate(${midX}, ${midY})`}>
                    <rect
                      x={-link.label.length * 3.2 - 6}
                      y={-7}
                      width={link.label.length * 6.4 + 12}
                      height={14}
                      rx={7}
                      fill="#0D1017"
                      fillOpacity={0.92}
                      stroke={strokeColor}
                      strokeWidth={0.8}
                      strokeOpacity={0.6}
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="central"
                      fill={isSelected ? '#D2F824' : '#8B949E'}
                      fontSize={8.5}
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {link.label}
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* DYNAMIC FORCE-DIRECTED PHYSICS NODES */}
          {nodes.map((node) => {
            if (node.x === undefined || node.y === undefined) return null;

            const isSelected = activeTarget && node.prospectId === activeTarget.id;
            const isHovered = hoveredNodeId === node.id;
            const isHub = node.category === 'hub';
            const isAuditingThis = isAuditing && auditingProspectId === node.prospectId;

            let fillColor = '#D2F824';
            let glowFilter = '';
            if (node.colorType === 'emerald') {
              fillColor = '#10B981';
              glowFilter = 'url(#glow-emerald)';
            } else if (node.colorType === 'rose') {
              fillColor = '#F43F5E';
            } else if (node.colorType === 'amber') {
              fillColor = '#F59E0B';
            } else if (node.colorType === 'blue') {
              fillColor = '#3B82F6';
            } else if (node.colorType === 'orange') {
              fillColor = '#F97316';
            } else if (node.colorType === 'purple') {
              fillColor = '#A855F7';
            } else if (node.colorType === 'cyan') {
              fillColor = '#06B6D4';
            }

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onMouseDown={(e) => handleNodeMouseDown(e, node)}
                onMouseEnter={() => setHoveredNodeId(node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
                className="cursor-pointer group"
                style={{ pointerEvents: 'auto' }}
              >
                {/* Ping wave for central Hub or active prospect */}
                {(isHub || isSelected || isAuditingThis) && (
                  <circle
                    r={node.radius + 10}
                    fill={fillColor}
                    fillOpacity={0.2}
                    className="animate-ping"
                  />
                )}

                {/* Outer halo */}
                {(isSelected || isHovered) && (
                  <circle
                    r={node.radius + 6}
                    fill="none"
                    stroke={fillColor}
                    strokeWidth={2}
                    strokeOpacity={0.8}
                    filter={glowFilter}
                  />
                )}

                {/* Base Node Circle with spring drag handle */}
                <circle
                  r={node.radius}
                  fill={fillColor}
                  stroke="#0D1017"
                  strokeWidth={2.5}
                  className="transition-transform duration-100 ease-out hover:scale-125"
                  style={{
                    filter: isSelected ? 'drop-shadow(0 0 10px #D2F824)' : undefined
                  }}
                />

                {/* Center glyph or icon badge */}
                {isHub ? (
                  <circle r={4} fill="#0D1017" />
                ) : isSelected ? (
                  <circle r={3.5} fill="#000" />
                ) : null}

                {/* Text Label Below Node (Matching MiroFish Typography) */}
                <g transform={`translate(0, ${node.radius + 12})`}>
                  <rect
                    x={-Math.min(node.label.length * 3.4, 75) - 6}
                    y={-7}
                    width={Math.min(node.label.length * 6.8, 150) + 12}
                    height={15}
                    rx={4}
                    fill="#121620"
                    fillOpacity={0.92}
                    stroke={isSelected ? '#D2F824' : isHovered ? '#60A5FA' : '#262D3D'}
                    strokeWidth={isSelected ? 1.2 : 0.8}
                  />
                  <text
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill={isSelected ? '#D2F824' : '#F3F4F6'}
                    fontSize={10}
                    fontFamily="monospace"
                    fontWeight={isSelected ? 'bold' : 'normal'}
                  >
                    {node.label.length > 20 ? `${node.label.slice(0, 19)}…` : node.label}
                  </text>
                </g>

                {/* Subtitle / Status tag if present */}
                {node.subLabel && (
                  <text
                    y={node.radius + 28}
                    textAnchor="middle"
                    fill="#8B949E"
                    fontSize={8}
                    fontFamily="monospace"
                  >
                    {node.subLabel}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* FIXED HUD OVERLAYS (Stationary & Non-Scaling) */}

      {/* 1. Compass / Orientation Rose in Top-Right (Radar Mode Only) */}
      {viewMode === 'radar' && (
        <div className="absolute top-14 right-4 z-20 w-24 h-24 rounded-full bg-[#161A23]/90 border border-[#262D3D]/80 backdrop-blur-md flex items-center justify-center shadow-xl pointer-events-none">
          <div className="relative w-20 h-20 rounded-full border border-dashed border-white/20 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border border-[#D2F824]/20 animate-compass"></div>
            <div className="flex flex-col items-center">
              <span className="text-[11px] font-mono font-bold text-[#D2F824] tracking-widest">NW</span>
              <div className="w-1 h-8 bg-gradient-to-b from-rose-500 via-amber-400 to-transparent rounded-full shadow-[0_0_8px_#f43f5e]"></div>
              <span className="text-[8px] font-mono text-[#586274]">312°</span>
            </div>
            <span className="absolute top-1 text-[8px] font-mono text-[#8B949E]">N</span>
            <span className="absolute bottom-1 text-[8px] font-mono text-[#586274]">S</span>
            <span className="absolute right-1 text-[8px] font-mono text-[#586274]">E</span>
            <span className="absolute left-1 text-[8px] font-mono text-[#586274]">W</span>
          </div>
        </div>
      )}

      {/* 2. OVERLAID ACTIVE INSPECTION CARD (Preserved 100% Fidelity) */}
      {activeTarget && showInspectorCard && (
        <div
          onMouseDown={(e) => e.stopPropagation()}
          className="absolute top-14 left-4 z-30 w-[92%] sm:w-[410px] bg-[#161A23]/95 backdrop-blur-xl border border-[#262D3D] rounded-xl p-4 shadow-2xl animate-in fade-in slide-in-from-left-2 pointer-events-auto"
        >
          {/* Header */}
          <div className="flex items-start justify-between pb-3 border-b border-[#262D3D]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#1C212D] border border-[#262D3D] flex items-center justify-center text-[#D2F824]">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white font-sans truncate max-w-[200px]">
                    {activeTarget.name}
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                    {activeTarget.auditCount > 0 ? 'Live Audit' : 'Target'}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-[#8B949E]">
                  {activeTarget.category} • {activeTarget.location.city}
                </span>
              </div>
            </div>
            <button
              onClick={() => setShowInspectorCard(false)}
              className="text-[#586274] hover:text-white transition-colors"
              title="Dismiss card"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Connection Status to Operator */}
          <div className="py-2.5 border-b border-[#262D3D]">
            {activeTarget.status === 'contacted' ? (
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs font-mono text-emerald-400">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="font-semibold">CONNECTED TO YOU</span>
                </div>
                <span className="text-[10px] text-emerald-300 font-mono">Sent via Gmail</span>
              </div>
            ) : activeTarget.status === 'draft_ready' ? (
              <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-between text-xs font-mono text-amber-400">
                <div className="flex items-center gap-1.5">
                  <Mail className="w-4 h-4 text-amber-400 shrink-0" />
                  <span className="font-semibold">DRAFT QUEUED</span>
                </div>
                <span className="text-[10px] text-amber-300 font-mono">Ready to Dispatch</span>
              </div>
            ) : (
              <div className="p-2 rounded-lg bg-[#1C212D] border border-[#262D3D] flex items-center justify-between text-xs font-mono text-[#8B949E]">
                <div className="flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-[#D2F824] shrink-0" />
                  <span>Recon Discovered</span>
                </div>
                <span className="text-[10px] text-[#586274]">Target Host Scanned</span>
              </div>
            )}
          </div>

          {/* Contact Route Path Progress */}
          <div className="py-3 border-b border-[#262D3D]/60">
            <div className="flex items-center justify-between text-xs font-mono mb-1.5">
              <span className="text-[#8B949E]">Target Host → Contact Form Path</span>
              <span
                className={`font-semibold ${
                  activeTarget.websiteStatus === 'broken_pages' || activeTarget.websiteStatus === 'unreachable'
                    ? 'text-rose-400'
                    : activeTarget.websiteStatus === 'ssl_expired'
                    ? 'text-amber-400'
                    : 'text-[#D2F824]'
                }`}
              >
                {activeTarget.websiteStatus === 'broken_pages'
                  ? 'HTTP 404 Failure'
                  : activeTarget.websiteStatus === 'ssl_expired'
                  ? 'TLS Expiring'
                  : activeTarget.websiteStatus === 'unreachable'
                  ? 'Host Unreachable'
                  : '200 OK Active'}
              </span>
            </div>
            <div className="w-full h-2 bg-[#1C212D] rounded-full overflow-hidden flex">
              <div
                className="h-full bg-[#D2F824] rounded-full shadow-[0_0_8px_#D2F824]"
                style={{ width: `${Math.min(activeTarget.opportunityScore, 85)}%` }}
              ></div>
              <div
                className="h-full bg-rose-500 rounded-r-full"
                style={{ width: `${Math.max(100 - activeTarget.opportunityScore, 15)}%` }}
              ></div>
            </div>
            <div className="flex items-center justify-between mt-2 text-[11px] font-mono text-[#586274]">
              <span className="flex items-center gap-1 text-[#8B949E]">
                <Timer className="w-3.5 h-3.5 text-[#D2F824]" /> Latency: ~73ms
              </span>
              <span>Crawled {activeTarget.auditCount * 6 + 12}/24 sub-routes</span>
            </div>
          </div>

          {/* Dual Gauges */}
          <div className="grid grid-cols-2 gap-3 pt-3">
            {/* Opportunity Gauge */}
            <div className="p-2.5 rounded-lg bg-[#1C212D] border border-[#262D3D] flex flex-col items-center relative overflow-hidden">
              <div className="w-full flex items-center justify-between text-[11px] font-mono text-[#8B949E] mb-1">
                <span>Audit Score</span>
                <span
                  className={`px-1 py-0.2 rounded text-[9px] font-bold border ${
                    activeTarget.opportunityScore >= 80
                      ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                      : 'bg-[#D2F824]/20 text-[#D2F824] border-[#D2F824]/30'
                  }`}
                >
                  {activeTarget.opportunityScore >= 80 ? 'HIGH ROI' : 'ACTIONABLE'}
                </span>
              </div>
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-24 h-24 -rotate-90">
                  <circle cx="48" cy="48" fill="transparent" r="38" stroke="#252B3B" strokeWidth="6"></circle>
                  <circle
                    className="drop-shadow-[0_0_6px_rgba(210,248,36,0.5)] transition-all duration-700"
                    cx="48"
                    cy="48"
                    fill="transparent"
                    r="38"
                    stroke="#D2F824"
                    strokeDasharray="238"
                    strokeDashoffset={238 - (238 * activeTarget.opportunityScore) / 100}
                    strokeLinecap="round"
                    strokeWidth="6"
                  ></circle>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-lg font-mono font-bold text-white">
                    {activeTarget.opportunityScore}
                    <span className="text-[11px] text-[#8B949E]">/100</span>
                  </span>
                </div>
              </div>
              <span className="text-[10px] font-mono text-[#D2F824] font-medium mt-0.5">
                High pitch viability
              </span>
            </div>

            {/* Server Latency Gauge */}
            <div className="p-2.5 rounded-lg bg-[#1C212D] border border-[#262D3D] flex flex-col items-center relative overflow-hidden">
              <div className="w-full flex items-center justify-between text-[11px] font-mono text-[#8B949E] mb-1">
                <span>Server Latency</span>
                <span className="px-1 py-0.2 rounded text-[9px] bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold">
                  {activeTarget.websiteStatus === 'active' ? 'OPTIMAL' : 'SLOW'}
                </span>
              </div>
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-24 h-24 -rotate-90">
                  <circle cx="48" cy="48" fill="transparent" r="38" stroke="#252B3B" strokeWidth="6"></circle>
                  <circle
                    cx="48"
                    cy="48"
                    fill="transparent"
                    r="38"
                    stroke="#F59E0B"
                    strokeDasharray="238"
                    strokeDashoffset="110"
                    strokeLinecap="round"
                    strokeWidth="6"
                  ></circle>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-lg font-mono font-bold text-white">
                    2.4<span className="text-[11px] text-[#8B949E]">s</span>
                  </span>
                  <span className="text-[9px] font-mono text-[#586274]">TTFB 73ms</span>
                </div>
              </div>
              <span className="text-[10px] font-mono text-amber-400 font-medium mt-0.5 truncate max-w-[140px]">
                {activeTarget.websiteStatus === 'active' ? 'Clean headers' : '3 uncompressed images'}
              </span>
            </div>
          </div>

          {/* Action Footer */}
          <div className="mt-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-2 overflow-hidden">
            <div className="flex items-center gap-2 text-xs font-mono text-amber-300 min-w-0 flex-1 mr-1">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="truncate">{activeTarget.recommendedAction}</span>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              <button
                onClick={(e) => onCreateDraft(activeTarget.id, e)}
                className={`px-2 py-1 rounded font-semibold text-[10px] font-mono transition-colors flex items-center gap-1 shrink-0 ${
                  activeTarget.status === 'contacted'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30'
                    : activeTarget.status === 'draft_ready'
                    ? 'bg-amber-400 text-black hover:bg-amber-300 shadow-[0_0_8px_rgba(245,158,11,0.3)]'
                    : 'bg-[#D2F824] text-black hover:bg-[#bce018] shadow-[0_0_8px_rgba(210,248,36,0.3)]'
                }`}
              >
                {activeTarget.status === 'contacted' ? (
                  <>
                    <Check className="w-3 h-3" />
                    <span>Sent via Gmail</span>
                  </>
                ) : activeTarget.status === 'draft_ready' ? (
                  <>
                    <Mail className="w-3 h-3" />
                    <span>Review Draft</span>
                  </>
                ) : (
                  <span>Draft Pitch</span>
                )}
              </button>
              <button
                onClick={(e) => onRunAudit(activeTarget.id, e)}
                disabled={isAuditing}
                className="p-1.5 rounded bg-[#1C212D] text-white hover:text-[#D2F824] border border-[#262D3D] transition-colors disabled:opacity-40 shrink-0"
                title="Run audit"
              >
                <Play className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. MIROFISH FLOATING STATUS PILL (Matching Image 2 & 3) */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
        <div className="px-4 py-2 rounded-2xl bg-[#161A23]/95 border border-[#262D3D] shadow-2xl backdrop-blur-md flex items-center gap-2.5 text-xs font-mono font-medium text-white">
          <span className="text-base">🧠</span>
          <span>
            {viewMode === 'graph'
              ? 'GraphRAG intelligence & prospect matrix updating in real-time'
              : 'Radar telemetry & force physics active in real-time'}
          </span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        </div>
      </div>

      {/* 4. MIROFISH ENTITY TYPES LEGEND (Bottom Left - Image 3) */}
      {viewMode === 'graph' && (
        <div
          onMouseDown={(e) => e.stopPropagation()}
          className="absolute bottom-3 left-4 z-20 p-2.5 rounded-xl bg-[#161A23]/95 border border-[#262D3D] shadow-xl backdrop-blur-md pointer-events-auto"
        >
          <span className="text-[9px] font-mono font-bold text-[#8B949E] tracking-wider uppercase block mb-1.5">
            Entity Types
          </span>
          <div className="flex items-center gap-3 text-[10px] font-mono text-[#F3F4F6]">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#F97316]"></span>
              Prospect Target
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]"></span>
              AI & Tech Stack
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]"></span>
              Connected
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#F43F5E]"></span>
              Critical Finding
            </span>
          </div>
        </div>
      )}

      {/* 5. BOTTOM UTILITIES & ZOOM TOOLS */}
      <div
        onMouseDown={(e) => e.stopPropagation()}
        className="absolute bottom-3 right-4 z-20 flex items-center gap-2 text-[11px] font-mono text-[#586274] pointer-events-auto"
      >
        <span className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#161A23]/80 border border-[#262D3D] text-[#8B949E]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#D2F824] animate-pulse"></span>
          Drag nodes • Drag bg to pan • Scroll to zoom
        </span>

        {/* Map Zoom Controls */}
        <div className="flex items-center bg-[#161A23]/90 border border-[#262D3D] rounded-lg p-0.5 shadow-lg">
          <button
            onClick={() => setShowInspectorCard(!showInspectorCard)}
            className={`p-1 transition-colors ${showInspectorCard ? 'text-[#D2F824]' : 'text-[#8B949E] hover:text-white'}`}
            title="Toggle Inspector Card"
          >
            <Layers className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setRadarZoom((z) => Math.min(z + 0.15, 2.4))}
            className="p-1 text-[#8B949E] hover:text-white transition-colors"
            title="Zoom In"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setRadarZoom((z) => Math.max(z - 0.15, 0.5))}
            className="p-1 text-[#8B949E] hover:text-white transition-colors"
            title="Zoom Out"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleResetView}
            className="p-1 text-[#8B949E] hover:text-white transition-colors"
            title="Reset View"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
