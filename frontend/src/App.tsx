import React, { useState, useEffect } from 'react';
import { useUiStore, uiStore } from './stores/useUiStore';
import { useOpportunities, useOpportunityWorkbench } from './hooks/useOpportunities';
import { useCases } from './hooks/useCases';
import { useExceptions } from './hooks/useExceptions';
import { useWebSocket } from './hooks/useWebSocket';
import { ApiService } from './services/api';
import { OpportunitySummary, ExceptionItem, QualityControlAuditSummary } from './types';
import { MetricCard } from './components/common/MetricCard';
import { Modal } from './components/common/Modal';
import { ExceptionResolve } from './components/forms/ExceptionResolve';

import { PipelineView } from './views/PipelineView';
import { CasesView } from './views/CasesView';
import { ExceptionsView } from './views/ExceptionsView';
import { InvestigatorView } from './views/InvestigatorView';
import { CountyRadarView } from './views/CountyRadarView';
import { DealRoomView } from './views/DealRoomView';

import { QcAuditModal } from './components/modals/QcAuditModal';
import { TransitionModal } from './components/modals/TransitionModal';
import { DossierModal } from './components/modals/DossierModal';

const TAB_TITLES: Record<string, string> = {
  pipeline: '14-Stage Opportunity Pipeline Workbench',
  county: 'Municipal Court Scraper & Intake Hub',
  exceptions: 'Quarantined Tasks & Exceptions Triage',
  investigator: 'Probate Opportunity File (POF) Investigator',
  counties: 'Washington Jurisdictional Radar',
  dealroom: 'Certified Wholesaler Deal Room & CRM Dispatch',
};

export const App: React.FC = () => {
  const { activeTab, selectedOpportunityId, selectedCounty, stageFilter, searchQuery, toasts } = useUiStore();
  const { isConnected } = useWebSocket();

  // Data hooks
  const { opportunities, loading: oppsLoading, refetch: refetchOpps, auditQC, advanceStage, deliverDeal } =
    useOpportunities(selectedCounty, stageFilter);
  const { cases, refetch: refetchCases, runScraper } = useCases(selectedCounty);
  const { exceptions, refetch: refetchExceptions, resolve: resolveException } = useExceptions();
  const { dossier, loading: dossierLoading } = useOpportunityWorkbench(selectedOpportunityId);

  // Modals state
  const [dossierModalOpen, setDossierModalOpen] = useState<boolean>(false);
  const [qcModalOpen, setQcModalOpen] = useState<boolean>(false);
  const [activeQcSummary, setActiveQcSummary] = useState<QualityControlAuditSummary | null>(null);
  const [transitionModalOpen, setTransitionModalOpen] = useState<boolean>(false);
  const [targetOppForTransition, setTargetOppForTransition] = useState<OpportunitySummary | null>(null);
  const [resolveModalOpen, setResolveModalOpen] = useState<boolean>(false);
  const [selectedException, setSelectedException] = useState<ExceptionItem | null>(null);

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

  // Derived KPI metrics
  const activeCount = opportunities.length;
  const priorityACount = opportunities.filter(
    (o) => (o.priority || '').toUpperCase().includes('A') || (o.priority || '').toUpperCase() === 'HIGH'
  ).length;
  const qcCertifiedCount = opportunities.filter(
    (o) => o.is_qc_certified || o.workflow_stage === 'READY' || o.workflow_stage === 'DELIVERED'
  ).length;
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

  const handleOpenTransition = (opp: OpportunitySummary) => {
    setTargetOppForTransition(opp);
    setTransitionModalOpen(true);
  };

  const handleOpenResolve = (exc: ExceptionItem) => {
    setSelectedException(exc);
    setResolveModalOpen(true);
  };

  const openDossier = (oppId: string) => {
    uiStore.setSelectedOpportunityId(oppId);
    setDossierModalOpen(true);
  };

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

      {/* Main Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between select-none">
        <div>
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
        {/* Top Header */}
        <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-slate-900/50 backdrop-blur shrink-0">
          <h2 className="text-base font-bold tracking-tight text-white font-mono">
            {TAB_TITLES[activeTab] || 'Decision Intelligence Platform'}
          </h2>

          <div className="flex items-center space-x-3">
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

          {/* Active Workspace View */}
          {activeTab === 'pipeline' && (
            <PipelineView
              opportunities={opportunities}
              loading={oppsLoading}
              searchQuery={searchQuery}
              stageFilter={stageFilter}
              onAuditQC={handleAuditQC}
              onOpenTransition={handleOpenTransition}
              onOpenDossier={openDossier}
            />
          )}

          {activeTab === 'county' && (
            <CasesView
              cases={cases}
              onTriggerScraper={runScraper}
            />
          )}

          {activeTab === 'exceptions' && (
            <ExceptionsView
              exceptions={exceptions}
              onOpenResolve={handleOpenResolve}
            />
          )}

          {activeTab === 'investigator' && (
            <InvestigatorView
              opportunities={opportunities}
              selectedOpportunityId={selectedOpportunityId}
              dossier={dossier}
              onOpenDossierModal={() => setDossierModalOpen(true)}
            />
          )}

          {activeTab === 'counties' && (
            <CountyRadarView
              countyBoard={countyBoard}
              loading={countyBoardLoading}
            />
          )}

          {activeTab === 'dealroom' && (
            <DealRoomView
              opportunities={opportunities}
              onOpenDossier={openDossier}
              onDeliverDeal={deliverDeal}
            />
          )}
        </div>
      </main>

      {/* QC Audit Modal */}
      <QcAuditModal
        isOpen={qcModalOpen}
        onClose={() => setQcModalOpen(false)}
        summary={activeQcSummary}
      />

      {/* FSM Transition Modal */}
      <TransitionModal
        isOpen={transitionModalOpen}
        onClose={() => {
          setTransitionModalOpen(false);
          setTargetOppForTransition(null);
        }}
        targetOpp={targetOppForTransition}
        onCommit={advanceStage}
      />

      {/* Exception Resolution Modal */}
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

      {/* Dossier Modal */}
      <DossierModal
        isOpen={dossierModalOpen}
        onClose={() => setDossierModalOpen(false)}
        dossier={dossier}
        loading={dossierLoading}
      />
    </div>
  );
};
