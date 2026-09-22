import React, { useState, useEffect } from 'react';
import { useUiStore, uiStore } from './stores/useUiStore';
import { useOpportunities, useOpportunityWorkbench } from './hooks/useOpportunities';
import { useCases } from './hooks/useCases';
import { useExceptions } from './hooks/useExceptions';
import { ApiService } from './services/api';
import { OpportunitySummary, QualityControlAuditSummary, ExceptionItem } from './types';
import { ToastHub } from './components/layout/ToastHub';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { WorkspaceContent } from './components/layout/WorkspaceContent';
import { AppModals } from './components/layout/AppModals';

export const App: React.FC = () => {
  const { activeTab, selectedOpportunityId, selectedCounty, stageFilter } = useUiStore();

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

  const handleRefreshAll = () => {
    refetchOpps();
    refetchCases();
    refetchExceptions();
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      <ToastHub />
      <Sidebar
        opportunitiesCount={opportunities.length}
        casesCount={cases.length}
        openExceptionsCount={exceptions.filter((e) => e.status !== 'RESOLVED').length}
      />
      <main className="flex-1 flex flex-col overflow-hidden bg-slate-950">
        <Header onRefresh={handleRefreshAll} />
        <WorkspaceContent
          opportunities={opportunities}
          oppsLoading={oppsLoading}
          cases={cases}
          exceptions={exceptions}
          dossier={dossier}
          dossierLoading={dossierLoading}
          countyBoard={countyBoard}
          countyBoardLoading={countyBoardLoading}
          onAuditQC={handleAuditQC}
          onOpenTransition={handleOpenTransition}
          onOpenResolve={handleOpenResolve}
          onOpenDossier={openDossier}
          onTriggerScraper={runScraper}
          onDeliverDeal={deliverDeal}
        />
      </main>
      <AppModals
        qcModalOpen={qcModalOpen}
        onCloseQcModal={() => setQcModalOpen(false)}
        activeQcSummary={activeQcSummary}
        transitionModalOpen={transitionModalOpen}
        onCloseTransitionModal={() => {
          setTransitionModalOpen(false);
          setTargetOppForTransition(null);
        }}
        targetOppForTransition={targetOppForTransition}
        onAdvanceStage={advanceStage}
        resolveModalOpen={resolveModalOpen}
        onCloseResolveModal={() => setResolveModalOpen(false)}
        selectedException={selectedException}
        onResolveException={resolveException}
        onReAuditOpportunity={handleAuditQC}
        opportunities={opportunities}
        dossierModalOpen={dossierModalOpen}
        onCloseDossierModal={() => setDossierModalOpen(false)}
        dossier={dossier}
        dossierLoading={dossierLoading}
      />
    </div>
  );
};
