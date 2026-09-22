import React, { useState, useEffect } from 'react';
import { useUiStore, WorkspaceTab, uiStore } from './stores/useUiStore';
import { useOpportunities, useOpportunityWorkbench } from './hooks/useOpportunities';
import { useCases } from './hooks/useCases';
import { useExceptions } from './hooks/useExceptions';
import { useWebSocket } from './hooks/useWebSocket';
import { ApiService } from './services/api';
import { OpportunitySummary, ExceptionItem, QualityControlAuditSummary, LifecycleStage } from './types';
import { Badge } from './components/common/Badge';
import { Modal } from './components/common/Modal';
import { Table, Column } from './components/common/Table';
import { MetricCard } from './components/common/MetricCard';
import { EquityWaterfall } from './components/pof/EquityWaterfall';
import { AuthorityBadge } from './components/pof/AuthorityBadge';
import { EvidenceViewer } from './components/pof/EvidenceViewer';
import { ControlMap } from './components/pof/ControlMap';
import { ScraperTrigger } from './components/forms/ScraperTrigger';
import { ExceptionResolve } from './components/forms/ExceptionResolve';

export const App: React.FC = () => {
  const { activeTab, selectedOpportunityId, selectedCounty, stageFilter, searchQuery, toasts } = useUiStore();
  const { isConnected } = useWebSocket();

  // Data hooks
  const { opportunities, loading: oppsLoading, refetch: refetchOpps, auditQC, advanceStage, deliverDeal } =
    useOpportunities(selectedCounty, stageFilter);
  const { cases, loading: casesLoading, refetch: refetchCases, runScraper } = useCases(selectedCounty);
  const { exceptions, loading: excsLoading, refetch: refetchExceptions, resolve: resolveException } = useExceptions();
  const { dossier, loading: dossierLoading } = useOpportunityWorkbench(selectedOpportunityId);

  // Modals state
  const [dossierModalOpen, setDossierModalOpen] = useState<boolean>(false);
  const [qcModalOpen, setQcModalOpen] = useState<boolean>(false);
  const [activeQcSummary, setActiveQcSummary] = useState<QualityControlAuditSummary | null>(null);
  const [transitionModalOpen, setTransitionModalOpen] = useState<boolean>(false);
  const [targetOppForTransition, setTargetOppForTransition] = useState<OpportunitySummary | null>(null);
  const [selectedTargetStage, setSelectedTargetStage] = useState<string>('QC');
  const [transitionNotes, setTransitionNotes] = useState<string>('');
  const [resolveModalOpen, setResolveModalOpen] = useState<boolean>(false);
  const [selectedException, setSelectedException] = useState<ExceptionItem | null>(null);
  const [pipelineViewMode, setPipelineViewMode] = useState<'table' | 'kanban'>('table');
  const [minEquityFilter, setMinEquityFilter] = useState<number>(30);
  const [aiPrompt, setAiPrompt] = useState<string>('');
  const [aiResponse, setAiResponse] = useState<string>('');
  const [aiLoading, setAiLoading] = useState<boolean>(false);

  // Live County Radar state
  const [countyBoard, setCountyBoard] = useState<any[]>([]);
  const [countyBoardLoading, setCountyBoardLoading] = useState<boolean>(false);

  useEffect(() => {
    if (activeTab === 'counties') {
      setCountyBoardLoading(true);
      ApiService.getCountyBoard()
        .then((data) => setCountyBoard(data || []))
        .catch(() => setCountyBoard([]))
        .finally(() => setCountyBoardLoading(false));
    }
  }, [activeTab]);

  // Filtering opportunities
  const filteredOpps = opportunities.filter((opp) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchNumber = (opp.case_number || '').toLowerCase().includes(q);
      const matchDec = (opp.decedent || opp.estate_name || '').toLowerCase().includes(q);
      const matchCounty = (opp.county_name || opp.county_id || '').toLowerCase().includes(q);
      if (!matchNumber && !matchDec && !matchCounty) return false;
    }
    return true;
  });

  // Calculate Metrics
  const activeCount = opportunities.length;
  const priorityACount = opportunities.filter((o) => (o.priority || '').toUpperCase().includes('A') || (o.priority || '').toUpperCase() === 'HIGH').length;
  const qcCertifiedCount = opportunities.filter((o) => o.is_qc_certified || o.workflow_stage === 'READY' || o.workflow_stage === 'DELIVERED').length;
  const openExceptionsCount = exceptions.filter((e) => e.status !== 'RESOLVED').length;

  const handleAuditQC = async (opp: OpportunitySummary) => {
    uiStore.addToast({
      type: 'info',
      title: 'Auditing 6 Gates',
      message: `Executing deterministic verification for ${opp.case_number}...`,
    });
    const result = await auditQC(opp.id);
    if (result) {
      setActiveQcSummary(result);
      setQcModalOpen(true);
    }
  };

  const openDossier = (oppId: string) => {
    uiStore.setSelectedOpportunityId(oppId);
    setDossierModalOpen(true);
  };

  const handleOpenTransition = (opp: OpportunitySummary) => {
    setTargetOppForTransition(opp);
    setSelectedTargetStage(opp.is_qc_certified ? 'DELIVERED' : 'QC');
    setTransitionNotes('');
    setTransitionModalOpen(true);
  };

  const handleCommitTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetOppForTransition) return;

    if (selectedTargetStage === 'DELIVERED' && !targetOppForTransition.is_qc_certified) {
      uiStore.addToast({
        type: 'error',
        title: 'Compliance Intercept',
        message: 'Strict Enforcement: Cannot transition to DELIVERED without passing all 6 Quality Gates (is_qc_certified === true).',
      });
      return;
    }

    const success = await advanceStage(targetOppForTransition.id, selectedTargetStage, transitionNotes);
    if (success) {
      setTransitionModalOpen(false);
      setTargetOppForTransition(null);
    }
  };

  const handleOpenResolve = (exc: ExceptionItem) => {
    setSelectedException(exc);
    setResolveModalOpen(true);
  };

  const handleAIInvestigate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiPrompt.trim()) return;
    setAiLoading(true);
    try {
      const res = await ApiService.investigateAI(aiPrompt, selectedOpportunityId || undefined);
      setAiResponse(res.narrative || res.response || JSON.stringify(res, null, 2));
    } catch (err: any) {
      setAiResponse(`[ERROR] AI Investigator inquiry failed: ${err.message}`);
    } finally {
      setAiLoading(false);
    }
  };

  // Normalizes ad-hoc and legacy backend stages to the canonical 14 FSM stages
  const normalizeStage = (opp: OpportunitySummary): LifecycleStage => {
    if (opp.lifecycle_stage) return opp.lifecycle_stage;
    const wf = (opp.workflow_stage || '').toUpperCase();
    if (wf === 'NEW' || wf === 'DISCOVERED') return 'DISCOVERED';
    if (wf === 'QC') return 'SCORED';
    if (wf === 'READY') return 'QC_CERTIFIED';
    if (wf === 'EXCEPTION') return 'SCORED';
    if (wf === 'DELIVERED') return 'DELIVERED';
    if (wf === 'CONTACTED') return 'CONTACTED';
    if (wf === 'APPOINTMENT') return 'APPOINTMENT';
    if (wf === 'OFFER') return 'OFFER';
    if (wf === 'CONTRACT') return 'CONTRACT';
    if (wf === 'CLOSED_WON') return 'CLOSED_WON';
    if (wf === 'CLOSED_LOST') return 'CLOSED_LOST';
    if (wf === 'ARCHIVED') return 'ARCHIVED';
    return 'DISCOVERED';
  };

  // 14 FSM stages for Kanban
  const KANBAN_STAGES: LifecycleStage[] = [
    'DISCOVERED',
    'PROPERTY_IDENTIFIED',
    'OWNERSHIP_RESOLVED',
    'CONTROL_MAPPED',
    'AUTHORITY_RESOLVED',
    'SCORED',
    'QC_CERTIFIED',
    'DELIVERED',
    'CONTACTED',
    'APPOINTMENT',
    'OFFER',
    'CONTRACT',
    'CLOSED_WON',
    'ARCHIVED',
  ];

  // Columns for Opportunities Table
  const oppColumns: Column<OpportunitySummary>[] = [
    {
      header: 'Case # / Decedent',
      render: (row) => (
        <div>
          <span className="font-mono font-bold text-indigo-400 block">{row.case_number}</span>
          <span className="text-slate-300 truncate max-w-[200px] block">{row.decedent || row.estate_name}</span>
          <span className="text-[10px] text-slate-500 font-mono">{row.county_name || row.county_id}</span>
        </div>
      ),
    },
    {
      header: 'Stage',
      render: (row) => <Badge type="stage" value={row.workflow_stage} />,
    },
    {
      header: 'Score / DFS',
      render: (row) => (
        <div className="font-mono">
          <span className="font-bold text-white">{row.score}</span>
          <span className="text-slate-500 text-[10px] block">DFS: -{Math.max(10, 100 - row.score)}</span>
        </div>
      ),
    },
    {
      header: 'Priority',
      render: (row) => <Badge type="priority" value={row.priority} />,
    },
    {
      header: 'Authority Scope',
      render: (row) => <Badge type="authority" value={row.authority_status} />,
    },
    {
      header: 'QC Certification',
      render: (row) => (
        <Badge
          type="gate"
          value={row.is_qc_certified || row.workflow_stage === 'READY' || row.workflow_stage === 'DELIVERED' ? 'QC_CERTIFIED' : 'PENDING'}
        />
      ),
    },
    {
      header: 'Actions',
      className: 'text-right',
      render: (row) => (
        <div className="flex items-center justify-end space-x-2">
          <button
            onClick={() => handleAuditQC(row)}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-mono text-[11px] border border-slate-700 active:scale-95 transition"
            title="Audit against 6 deterministic quality gates"
          >
            Audit 6 Gates
          </button>
          <button
            onClick={() => handleOpenTransition(row)}
            className="px-2.5 py-1 bg-indigo-900/50 hover:bg-indigo-800 text-indigo-200 rounded font-mono text-[11px] border border-indigo-700/60 active:scale-95 transition"
            title="Advance FSM lifecycle stage"
          >
            Advance
          </button>
          <button
            onClick={() => openDossier(row.id)}
            className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-mono text-[11px] shadow-sm shadow-indigo-600/30 active:scale-95 transition"
          >
            Dossier &rarr;
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Toast Notification Hub */}
      <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`p-3.5 rounded-xl border shadow-xl backdrop-blur-md pointer-events-auto transition-all duration-300 ${
              toast.type === 'error'
                ? 'bg-rose-950/90 border-rose-800 text-rose-200'
                : toast.type === 'success'
                ? 'bg-emerald-950/90 border-emerald-800 text-emerald-200'
                : toast.type === 'warning'
                ? 'bg-amber-950/90 border-amber-800 text-amber-200'
                : 'bg-slate-900/90 border-slate-700 text-slate-200'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono uppercase">{toast.title}</span>
              <button
                onClick={() => uiStore.removeToast(toast.id)}
                className="text-xs opacity-60 hover:opacity-100 ml-2"
              >
                ✕
              </button>
            </div>
            <p className="text-xs mt-1 font-sans">{toast.message}</p>
          </div>
        ))}
      </div>

      {/* Main Application Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between select-none">
        <div>
          {/* Logo & Header */}
          <div className="p-6 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <span className="text-xl font-black tracking-widest text-indigo-400">GIENI OS</span>
              <span className="text-[10px] bg-indigo-900/80 text-indigo-300 font-mono px-1.5 py-0.5 rounded border border-indigo-700">
                PROD
              </span>
            </div>
            <p className="text-[11px] text-slate-500 tracking-wider mt-1 font-mono">
              DECISION INTELLIGENCE v2.0
            </p>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5">
            <div className="px-2 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono">
              Workspaces
            </div>

            <button
              onClick={() => uiStore.setActiveTab('pipeline')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'pipeline'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span>📊</span>
                <span>1. Pipeline Workbench</span>
              </div>
              <span className="text-[10px] font-mono opacity-80">{opportunities.length}</span>
            </button>

            <button
              onClick={() => uiStore.setActiveTab('county')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'county'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span>🏛️</span>
                <span>2. County Intake Hub</span>
              </div>
              <span className="text-[10px] font-mono opacity-80">{cases.length}</span>
            </button>

            <button
              onClick={() => uiStore.setActiveTab('exceptions')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'exceptions'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span>⚠️</span>
                <span>3. Tasks & Exceptions</span>
              </div>
              {openExceptionsCount > 0 && (
                <span className="text-[10px] font-mono font-black bg-rose-600 text-white px-1.5 py-0.5 rounded-full animate-pulse">
                  {openExceptionsCount}
                </span>
              )}
            </button>

            <button
              onClick={() => uiStore.setActiveTab('investigator')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'investigator'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span>🔍</span>
                <span>4. Property Investigator</span>
              </div>
              <span className="text-[10px] font-mono text-indigo-300">POF</span>
            </button>

            <div className="pt-4 px-2 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono">
              Market Intelligence
            </div>

            <button
              onClick={() => uiStore.setActiveTab('counties')}
              className={`w-full flex items-center px-3.5 py-2.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'counties'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <span className="mr-2.5">🗺️</span>
              <span>5. County Radar</span>
            </button>

            <button
              onClick={() => uiStore.setActiveTab('dealroom')}
              className={`w-full flex items-center px-3.5 py-2.5 text-xs font-semibold rounded-lg transition ${
                activeTab === 'dealroom'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <span className="mr-2.5">🤝</span>
              <span>6. Wholesaler Deal Room</span>
            </button>
          </nav>
        </div>

        {/* Telemetry Indicator */}
        <div className="p-4 border-t border-slate-800 text-xs text-slate-500 bg-slate-950/40">
          <div className="flex items-center space-x-2.5">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
              }`}
            />
            <span className="font-semibold text-slate-300 font-mono">
              {isConnected ? 'Telemetry Online' : 'Connecting WS'}
            </span>
          </div>
          <div className="text-[10px] text-slate-500 mt-1 font-mono">
            Direct Live I/O · Washington Title 11
          </div>
        </div>
      </aside>

      {/* Main Workspace Area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-slate-950">
        {/* Top Control Bar */}
        <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-slate-900/50 backdrop-blur shrink-0">
          <div className="flex items-center space-x-4">
            <h2 className="text-base font-bold tracking-tight text-white font-mono">
              {activeTab === 'pipeline' && '14-Stage Opportunity Pipeline Workbench'}
              {activeTab === 'county' && 'Municipal Court Scraper & Intake Hub'}
              {activeTab === 'exceptions' && 'Quarantined Tasks & Exceptions Triage'}
              {activeTab === 'investigator' && 'Probate Opportunity File (POF) Investigator'}
              {activeTab === 'counties' && 'Washington Jurisdictional Radar'}
              {activeTab === 'dealroom' && 'Certified Wholesaler Deal Room & CRM Dispatch'}
            </h2>
          </div>

          <div className="flex items-center space-x-3">
            {/* Global Territory Selector */}
            <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
              <label htmlFor="territory-select" className="text-[11px] font-mono text-slate-400">Territory:</label>
              <select
                id="territory-select"
                value={selectedCounty}
                onChange={(e) => uiStore.setSelectedCounty(e.target.value)}
                className="bg-transparent text-xs font-mono text-white focus:outline-none cursor-pointer"
              >
                <option value="ALL">All Washington Territories</option>
                <option value="Thurston">Thurston County (53067)</option>
                <option value="Pierce">Pierce County (53053)</option>
                <option value="King">King County (53033)</option>
                <option value="Snohomish">Snohomish County (53061)</option>
              </select>
            </div>

            {/* Refresh Live State */}
            <button
              onClick={() => {
                refetchOpps();
                refetchCases();
                refetchExceptions();
                uiStore.addToast({
                  type: 'info',
                  title: 'State Synchronized',
                  message: 'Synchronized live state from Platform API.',
                });
              }}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 active:scale-95 transition text-xs font-semibold rounded-lg border border-slate-700 flex items-center space-x-1.5"
            >
              <span>⟳</span>
              <span>Refresh Live State</span>
            </button>
          </div>
        </header>

        {/* Scrollable Content Container */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {/* Top KPI Metrics Bar */}
          <div className="grid grid-cols-4 gap-4">
            <MetricCard
              label="Active Pipeline"
              value={activeCount}
              subtext="Total opportunities tracked"
              trend="+12% wk"
              trendPositive
              icon="📊"
            />
            <MetricCard
              label="Priority A (High)"
              value={priorityACount}
              subtext="4-Hour SLA direct dispatch"
              trend="Urgent"
              trendPositive={false}
              icon="🚨"
            />
            <MetricCard
              label="QC Certified Deals"
              value={`${qcCertifiedCount} / ${activeCount}`}
              subtext="Passed all 6 Quality Gates"
              trend="100% Validated"
              trendPositive
              icon="🛡️"
            />
            <MetricCard
              label="Open Exceptions"
              value={openExceptionsCount}
              subtext="Quarantined records in triage"
              trend={openExceptionsCount > 0 ? 'Action Req' : 'Clear'}
              trendPositive={openExceptionsCount === 0}
              icon="⚠️"
            />
          </div>

          {/* WORKSPACE 1: PIPELINE WORKBENCH */}
          {activeTab === 'pipeline' && (
            <div className="space-y-6">
              {/* Filter & View Bar */}
              <div className="flex items-center justify-between gap-4 p-4 bg-slate-900 border border-slate-800 rounded-xl">
                <div className="flex items-center space-x-4 flex-1">
                  {/* Search Input */}
                  <div className="relative flex-1 max-w-sm">
                    <input
                      type="text"
                      placeholder="Search case #, decedent, county..."
                      value={searchQuery}
                      onChange={(e) => uiStore.setSearchQuery(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  {/* Stage Filter */}
                  <div className="flex items-center space-x-2">
                    <label htmlFor="stage-filter-select" className="text-xs font-mono text-slate-400">Stage:</label>
                    <select
                      id="stage-filter-select"
                      value={stageFilter}
                      onChange={(e) => uiStore.setStageFilter(e.target.value)}
                      className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono focus:outline-none"
                    >
                      <option value="ALL">All Stages</option>
                      <option value="SCORED">SCORED</option>
                      <option value="QC">QC</option>
                      <option value="READY">READY</option>
                      <option value="DELIVERED">DELIVERED</option>
                      <option value="EXCEPTION">EXCEPTION</option>
                    </select>
                  </div>

                  {/* Min Equity Slider */}
                  <div className="flex items-center space-x-2">
                    <label htmlFor="min-equity-slider" className="text-xs font-mono text-slate-400">Min Equity:</label>
                    <input
                      id="min-equity-slider"
                      type="range"
                      min={30}
                      max={100}
                      value={minEquityFilter}
                      onChange={(e) => setMinEquityFilter(Number(e.target.value))}
                      className="w-20 h-1 bg-slate-800 rounded appearance-none cursor-pointer accent-indigo-500"
                    />
                    <span className="text-xs font-mono text-slate-300 font-bold">{minEquityFilter}%</span>
                  </div>
                </div>

                {/* View Mode Toggle */}
                <div className="flex items-center space-x-1 bg-slate-950 p-1 border border-slate-800 rounded-lg">
                  <button
                    onClick={() => setPipelineViewMode('table')}
                    className={`px-3 py-1 text-xs font-mono rounded ${
                      pipelineViewMode === 'table' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Dense Table
                  </button>
                  <button
                    onClick={() => setPipelineViewMode('kanban')}
                    className={`px-3 py-1 text-xs font-mono rounded ${
                      pipelineViewMode === 'kanban' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    14-Stage Kanban
                  </button>
                </div>
              </div>

              {/* View Rendering */}
              {pipelineViewMode === 'table' ? (
                oppsLoading ? (
                  <div className="p-12 text-center font-mono text-slate-400">Loading live opportunities...</div>
                ) : (
                  <Table
                    columns={oppColumns}
                    data={filteredOpps}
                    keyField="id"
                    emptyMessage="No opportunities found matching search criteria."
                  />
                )
              ) : (
                /* Kanban View */
                <div className="flex space-x-4 overflow-x-auto pb-4">
                  {KANBAN_STAGES.map((stage) => {
                    const stageOpps = filteredOpps.filter((o) => normalizeStage(o) === stage);
                    return (
                      <div
                        key={stage}
                        className="w-72 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col shrink-0 min-h-[500px]"
                      >
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                          <span className="text-xs font-mono font-bold text-slate-200 truncate">{stage}</span>
                          <span className="text-[10px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
                            {stageOpps.length}
                          </span>
                        </div>
                        <div className="space-y-3 flex-1 overflow-y-auto">
                          {stageOpps.map((opp) => (
                            <div
                              key={opp.id}
                              className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2 hover:border-indigo-500/50 transition cursor-pointer"
                              onClick={() => openDossier(opp.id)}
                            >
                              <div className="flex justify-between items-start">
                                <span className="text-xs font-mono font-bold text-indigo-400">{opp.case_number}</span>
                                <Badge type="priority" value={opp.priority} />
                              </div>
                              <p className="text-xs text-slate-300 font-semibold truncate">{opp.decedent || opp.estate_name}</p>
                              <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-900">
                                <span>Score: {opp.score}</span>
                                <span>{opp.county_name || opp.county_id}</span>
                              </div>
                            </div>
                          ))}
                          {stageOpps.length === 0 && (
                            <div className="text-center text-[11px] text-slate-600 font-mono py-8">No records</div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* WORKSPACE 2: MUNICIPAL INTAKE HUB */}
          {activeTab === 'county' && (
            <div className="space-y-6">
              <ScraperTrigger onTrigger={runScraper} />

              {/* Ingested Cases Table */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                      Ingested Municipal Dockets
                    </h3>
                    <p className="text-xs text-slate-400 font-sans">
                      Washington Superior Court Filings Indexed Live into Database
                    </p>
                  </div>
                  <span className="text-xs font-mono text-slate-400">Total Cases: {cases.length}</span>
                </div>

                <Table
                  columns={[
                    {
                      header: 'Case Number',
                      accessor: 'case_number',
                      render: (row) => <span className="font-mono font-bold text-indigo-400">{row.case_number}</span>,
                    },
                    { header: 'County ID', accessor: 'county_id' },
                    { header: 'Decedent / Estate', accessor: 'decedent' },
                    { header: 'Filing Date', accessor: 'filing_date' },
                    {
                      header: 'Status',
                      render: (row) => (
                        <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">
                          {row.status}
                        </span>
                      ),
                    },
                  ]}
                  data={cases}
                  keyField="id"
                  emptyMessage="No municipal cases recorded yet. Launch the headless scraper above."
                />
              </div>
            </div>
          )}

          {/* WORKSPACE 3: TASKS & EXCEPTIONS */}
          {activeTab === 'exceptions' && (
            <div className="space-y-6">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                      Quarantined Exception Queue
                    </h3>
                    <p className="text-xs text-slate-400 font-sans">
                      Records Flagged by Gates 1–6 Requiring Human Review & Remediation
                    </p>
                  </div>
                  <span className="text-xs font-mono text-slate-400">Active Exceptions: {exceptions.length}</span>
                </div>

                <Table
                  columns={[
                    {
                      header: 'Exception ID / Opportunity',
                      render: (row) => (
                        <div>
                          <span className="font-mono font-bold text-slate-200 block">{row.id}</span>
                          <span className="text-[10px] font-mono text-indigo-400">{row.opportunity_id}</span>
                        </div>
                      ),
                    },
                    {
                      header: 'Gate / Failure Reason',
                      render: (row) => (
                        <div>
                          <span className="font-mono font-bold text-amber-400 block">{row.type}</span>
                          <span className="text-xs text-slate-400">{row.notes || 'Quarantined for verification'}</span>
                        </div>
                      ),
                    },
                    {
                      header: 'Urgency',
                      render: (row) => (
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                            row.severity === 'CRITICAL'
                              ? 'bg-rose-600 text-white animate-pulse'
                              : 'bg-amber-600 text-white'
                          }`}
                        >
                          {row.severity}
                        </span>
                      ),
                    },
                    {
                      header: 'SLA Remaining',
                      render: (row) => (
                        <span className="font-mono text-xs font-bold text-slate-300">
                          {row.sla_hours_remaining ? `${row.sla_hours_remaining}h : 00m` : '24h : 00m'}
                        </span>
                      ),
                    },
                    {
                      header: 'Status',
                      render: (row) => (
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                            row.status === 'RESOLVED'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : 'bg-amber-950 text-amber-400 border border-amber-800'
                          }`}
                        >
                          {row.status}
                        </span>
                      ),
                    },
                    {
                      header: 'Action',
                      className: 'text-right',
                      render: (row) => (
                        <button
                          disabled={row.status === 'RESOLVED'}
                          onClick={() => handleOpenResolve(row)}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded font-mono text-xs font-bold transition"
                        >
                          {row.status === 'RESOLVED' ? 'Resolved' : 'Resolve Triage'}
                        </button>
                      ),
                    },
                  ]}
                  data={exceptions}
                  keyField="id"
                  emptyMessage="All quality gates passing cleanly. Zero quarantined records."
                />
              </div>
            </div>
          )}

          {/* WORKSPACE 4: PROPERTY INVESTIGATOR */}
          {activeTab === 'investigator' && (
            <div className="space-y-6">
              {/* Target Selector */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <label htmlFor="target-opportunity-select" className="text-xs font-mono text-slate-400">Target Opportunity:</label>
                  <select
                    id="target-opportunity-select"
                    value={selectedOpportunityId || ''}
                    onChange={(e) => uiStore.setSelectedOpportunityId(e.target.value)}
                    className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none"
                  >
                    <option value="">Select Opportunity to Investigate...</option>
                    {opportunities.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.case_number} · {o.decedent || o.estate_name} ({o.county_name || o.county_id})
                      </option>
                    ))}
                  </select>
                </div>

                {selectedOpportunityId && (
                  <button
                    onClick={() => setDossierModalOpen(true)}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-mono font-bold transition"
                  >
                    Open Deep Dossier Modal
                  </button>
                )}
              </div>

              {/* POF Render */}
              {dossier ? (
                <div className="space-y-6">
                  <EquityWaterfall
                    ownership={dossier.ownership_summary}
                    avmValue={dossier.property_summary.avm_market_estimate || 450000}
                  />

                  <div className="grid grid-cols-2 gap-6">
                    <AuthorityBadge authority={dossier.authority_summary} />
                    <ControlMap
                      contact={dossier.contact_summary}
                      risk={dossier.risk_summary}
                      action={dossier.recommended_action}
                    />
                  </div>

                  <EvidenceViewer
                    evidence={dossier.evidence_summary}
                    caseNumber={dossier.opportunity.case_number}
                  />
                </div>
              ) : (
                <div className="p-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
                  <p className="text-sm font-mono text-slate-400">
                    Select an active opportunity above to inspect the canonical 8-Profile Probate Opportunity File (POF).
                  </p>
                </div>
              )}

              {/* AI Investigator Live Console */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                <div className="border-b border-slate-800 pb-3">
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                    AI Lead Investigator & Statutory Assistant
                  </h4>
                  <p className="text-xs text-slate-400 font-sans">
                    Ask questions regarding deed chain integrity, statutory authority (RCW Title 11), or heir consensus
                  </p>
                </div>

                <form onSubmit={handleAIInvestigate} className="flex gap-3">
                  <input
                    type="text"
                    placeholder="e.g. Verify RCW 11.68 powers and check if Letters Testamentary grant nonintervention sale authority..."
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    type="submit"
                    disabled={aiLoading}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg font-mono text-xs font-bold transition"
                  >
                    {aiLoading ? 'Querying...' : 'Investigate'}
                  </button>
                </form>

                {aiResponse && (
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 whitespace-pre-wrap">
                    {aiResponse}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* WORKSPACE 5: COUNTY RADAR */}
          {activeTab === 'counties' && (
            <div className="space-y-6">
              {countyBoardLoading ? (
                <div className="text-center py-16 text-slate-500 font-mono text-sm">
                  Loading jurisdictional court feeds & county intelligence...
                </div>
              ) : countyBoard.length === 0 ? (
                <div className="text-center py-16 text-slate-500 font-mono text-sm">
                  No active counties indexed in platform database.
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-6">
                  {countyBoard.map((c) => (
                    <div key={c.county_id || c.name} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 hover:border-emerald-500/30 transition">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-base font-bold text-white font-mono">{c.name} County, {c.state || 'WA'}</h4>
                          <span className="text-xs font-mono text-slate-400">Jurisdiction Tier: {c.tier || 1} · Portal: {c.court_portal}</span>
                        </div>
                        <span className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold ${
                          c.status === 'ACTIVE'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}>
                          {c.status || 'ACTIVE'}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 py-2 bg-slate-950/60 rounded-lg p-3 border border-slate-800/80 text-center font-mono">
                        <div>
                          <div className="text-[10px] text-slate-500 uppercase tracking-wider">Active Dockets</div>
                          <div className="text-sm font-bold text-white mt-0.5">{c.cases_count}</div>
                        </div>
                        <div>
                          <div className="text-[10px] text-slate-500 uppercase tracking-wider">Qualified Leads</div>
                          <div className="text-sm font-bold text-emerald-400 mt-0.5">{c.opportunities_count}</div>
                        </div>
                        <div>
                          <div className="text-[10px] text-slate-500 uppercase tracking-wider">Expansion Score</div>
                          <div className="text-sm font-bold text-blue-400 mt-0.5">{c.expansion_score} / 100</div>
                        </div>
                      </div>
                      <div className="space-y-1.5 text-xs font-mono text-slate-300 pt-2 border-t border-slate-800">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Median Home Value:</span>
                          <span className="font-semibold text-slate-200">
                            {c.median_home_price ? `$${c.median_home_price.toLocaleString()}` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Pipeline Conversion:</span>
                          <span className="text-emerald-400 font-bold">
                            {c.conversion_rate !== null && c.conversion_rate !== undefined ? `${c.conversion_rate}%` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Strategic Disposition:</span>
                          <span className="text-amber-400 font-medium">{c.recommendation}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* WORKSPACE 6: WHOLESALER DEAL ROOM */}
          {activeTab === 'dealroom' && (
            <div className="space-y-6">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                    Certified Wholesaler Deal Delivery Engine
                  </h3>
                  <p className="text-xs text-slate-400 font-sans">
                    Pre-cleared off-market inventory ready for immediate assignment & CRM dispatch
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  {opportunities
                    .filter((o) => o.is_qc_certified || o.workflow_stage === 'READY' || o.workflow_stage === 'DELIVERED')
                    .map((deal) => (
                      <div
                        key={deal.id}
                        className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4 hover:border-emerald-500/40 transition"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="text-xs font-mono text-indigo-400 font-bold">{deal.case_number}</span>
                            <h4 className="text-sm font-bold text-white mt-0.5">{deal.decedent || deal.estate_name}</h4>
                            <span className="text-[11px] text-slate-400 font-mono">{deal.county_name || deal.county_id}</span>
                          </div>
                          <Badge type="priority" value={deal.priority} />
                        </div>

                        <div className="space-y-1 text-xs font-mono text-slate-300 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Viability Score:</span>
                            <span className="text-emerald-400 font-bold">{deal.score} / 100</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Authority:</span>
                            <span className="text-slate-200">{deal.authority_status}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Delivery Status:</span>
                            <span className={deal.workflow_stage === 'DELIVERED' ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                              {deal.workflow_stage}
                            </span>
                          </div>
                        </div>

                        <div className="flex space-x-3">
                          <button
                            onClick={() => openDossier(deal.id)}
                            className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-mono font-bold transition"
                          >
                            View Dossier
                          </button>
                          <button
                            onClick={async () => {
                              try {
                                const targetUrl = window.prompt(
                                  'Enter Partner CRM Webhook URL (e.g. https://httpbin.org/post):',
                                  'https://httpbin.org/post'
                                );
                                if (!targetUrl) return;
                                const res = await ApiService.exportCrm(deal.id, targetUrl);
                                uiStore.addToast({
                                  type: 'success',
                                  title: 'CRM Dispatched',
                                  message: res.message || `Dispatched webhook payload for ${deal.case_number}`,
                                });
                                deliverDeal(deal.id, 'Dispatched to CRM partner webhook');
                              } catch (err: any) {
                                uiStore.addToast({
                                  type: 'error',
                                  title: 'Dispatch Failed',
                                  message: err.message,
                                });
                              }
                            }}
                            className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold shadow-lg shadow-emerald-600/20 transition"
                          >
                            Dispatch to CRM
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* QC AUDIT RESULT MODAL */}
      <Modal
        isOpen={qcModalOpen}
        onClose={() => setQcModalOpen(false)}
        title="Quality Control Audit Report (6 Deterministic Gates)"
        subtitle={`Audit results for Opportunity ${activeQcSummary?.opportunity_id}`}
      >
        {activeQcSummary && (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-slate-950 rounded-lg border border-slate-800">
              <div>
                <span className="text-xs font-mono text-slate-400 block">Overall Certification Status:</span>
                <span
                  className={`text-base font-mono font-bold ${
                    activeQcSummary.is_fully_certified ? 'text-emerald-400' : 'text-amber-400'
                  }`}
                >
                  {activeQcSummary.is_fully_certified ? '✓ FULLY CERTIFIED' : '⚠ GATE INTERCEPTED'}
                </span>
              </div>
              <Badge
                type="gate"
                value={activeQcSummary.is_fully_certified ? 'QC_CERTIFIED' : 'GATE_FAILED'}
              />
            </div>

            <div className="space-y-2">
              <h5 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                Gate-by-Gate Verification Matrix:
              </h5>
              <div className="space-y-2">
                {activeQcSummary.gate_results.map((g) => (
                  <div
                    key={g.gate_number}
                    className={`p-3 rounded-lg border flex items-center justify-between text-xs font-mono ${
                      g.passed
                        ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-200'
                        : 'bg-amber-950/40 border-amber-800/60 text-amber-200'
                    }`}
                  >
                    <div>
                      <span className="font-bold mr-2">Gate {g.gate_number}:</span>
                      <span>{g.gate_name}</span>
                      {g.failure_reason && (
                        <div className="text-[11px] text-rose-400 mt-1 font-sans">
                          Intercept Reason: {g.failure_reason}
                        </div>
                      )}
                    </div>
                    <span className="font-bold">{g.passed ? '✓ PASSED' : '✕ INTERCEPT'}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                onClick={() => setQcModalOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-mono"
              >
                Close Audit Report
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* FSM TRANSITION MODAL */}
      <Modal
        isOpen={transitionModalOpen}
        onClose={() => setTransitionModalOpen(false)}
        title="Advance FSM Lifecycle Stage"
        subtitle={`Validate transition for ${targetOppForTransition?.case_number}`}
        maxWidth="max-w-md"
      >
        <form onSubmit={handleCommitTransition} className="space-y-4">
          <div>
            <label htmlFor="target-stage-select" className="block text-xs font-mono text-slate-300 mb-1">Target Lifecycle Stage</label>
            <select
              id="target-stage-select"
              value={selectedTargetStage}
              onChange={(e) => setSelectedTargetStage(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            >
              <option value="SCORED">SCORED</option>
              <option value="QC">QC</option>
              <option value="READY">READY</option>
              <option value="DELIVERED">DELIVERED (Requires QC Certification)</option>
              <option value="CONTACTED">CONTACTED</option>
              <option value="OFFER">OFFER</option>
              <option value="CLOSED_WON">CLOSED_WON</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>
          </div>

          <div>
            <label htmlFor="transition-audit-notes" className="block text-xs font-mono text-slate-300 mb-1">Operator Notes</label>
            <input
              id="transition-audit-notes"
              type="text"
              placeholder="Reason for stage transition..."
              value={transitionNotes}
              onChange={(e) => setTransitionNotes(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-sans focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setTransitionModalOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-mono"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-mono font-bold"
            >
              Commit Transition
            </button>
          </div>
        </form>
      </Modal>

      {/* EXCEPTION RESOLUTION MODAL */}
      <Modal
        isOpen={resolveModalOpen}
        onClose={() => setResolveModalOpen(false)}
        title="Resolve Quarantined Exception"
        subtitle={`Correction Protocol for Exception ${selectedException?.id}`}
      >
        {selectedException && (
          <ExceptionResolve
            exception={selectedException}
            onCommit={resolveException}
            onCancel={() => setResolveModalOpen(false)}
            onReAudit={(oppId) => {
              setResolveModalOpen(false);
              const opp = opportunities.find((o) => o.id === oppId);
              if (opp) handleAuditQC(opp);
            }}
          />
        )}
      </Modal>

      {/* DEEP DOSSIER REVIEW MODAL */}
      <Modal
        isOpen={dossierModalOpen}
        onClose={() => setDossierModalOpen(false)}
        title={`Probate Opportunity File (POF): ${dossier?.opportunity.case_number || 'Loading...'}`}
        subtitle={`8-Profile Canonical Dossier · ${dossier?.opportunity.estate_name || ''}`}
        maxWidth="max-w-5xl"
      >
        {dossierLoading ? (
          <div className="p-16 text-center font-mono text-slate-400">Loading comprehensive 8-profile POF dossier...</div>
        ) : dossier ? (
          <div className="space-y-6">
            <EquityWaterfall
              ownership={dossier.ownership_summary}
              avmValue={dossier.property_summary.avm_market_estimate || 450000}
            />

            <div className="grid grid-cols-2 gap-6">
              <AuthorityBadge authority={dossier.authority_summary} />
              <ControlMap
                contact={dossier.contact_summary}
                risk={dossier.risk_summary}
                action={dossier.recommended_action}
              />
            </div>

            <EvidenceViewer
              evidence={dossier.evidence_summary}
              caseNumber={dossier.opportunity.case_number}
            />
          </div>
        ) : (
          <div className="p-12 text-center text-slate-400 font-mono">Dossier unavailable.</div>
        )}
      </Modal>
    </div>
  );
};
