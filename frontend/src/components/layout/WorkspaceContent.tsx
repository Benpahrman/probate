import React from 'react';
import { useUiStore } from '../../stores/useUiStore';
import { MetricCard } from '../common/MetricCard';
import { PipelineView } from '../../views/PipelineView';
import { CasesView } from '../../views/CasesView';
import { ExceptionsView } from '../../views/ExceptionsView';
import { InvestigatorView } from '../../views/InvestigatorView';
import { CountyRadarView } from '../../views/CountyRadarView';
import { DealRoomView } from '../../views/DealRoomView';
import { OpportunitySummary, CaseItem, ExceptionItem, FullPOFDossier } from '../../types';

interface WorkspaceContentProps {
  opportunities: OpportunitySummary[];
  oppsLoading: boolean;
  cases: CaseItem[];
  exceptions: ExceptionItem[];
  dossier: FullPOFDossier | null;
  dossierLoading: boolean;
  countyBoard: any[];
  countyBoardLoading: boolean;
  onAuditQC: (opp: OpportunitySummary) => void;
  onOpenTransition: (opp: OpportunitySummary) => void;
  onOpenResolve: (exc: ExceptionItem) => void;
  onOpenDossier: (oppId: string) => void;
  onTriggerScraper: (inputs: any) => Promise<any>;
  onDeliverDeal: (oppId: string, partnerId?: string) => Promise<boolean>;
}

export const WorkspaceContent: React.FC<WorkspaceContentProps> = ({
  opportunities,
  oppsLoading,
  cases,
  exceptions,
  dossier,
  dossierLoading,
  countyBoard,
  countyBoardLoading,
  onAuditQC,
  onOpenTransition,
  onOpenResolve,
  onOpenDossier,
  onTriggerScraper,
  onDeliverDeal,
}) => {
  const { activeTab, searchQuery, stageFilter, selectedOpportunityId } = useUiStore();

  const activeCount = opportunities.length;
  const priorityACount = opportunities.filter(
    (o) => (o.priority || '').toUpperCase().includes('A') || (o.priority || '').toUpperCase() === 'HIGH'
  ).length;
  const qcCertifiedCount = opportunities.filter(
    (o) => o.is_qc_certified || o.workflow_stage === 'READY' || o.workflow_stage === 'DELIVERED'
  ).length;
  const openExceptionsCount = exceptions.filter((e) => e.status !== 'RESOLVED').length;

  const renderActiveView = () => {
    switch (activeTab) {
      case 'pipeline':
        return (
          <PipelineView
            opportunities={opportunities}
            loading={oppsLoading}
            searchQuery={searchQuery}
            stageFilter={stageFilter}
            onAuditQC={onAuditQC}
            onOpenTransition={onOpenTransition}
            onOpenDossier={onOpenDossier}
          />
        );
      case 'county':
        return <CasesView cases={cases} onTriggerScraper={onTriggerScraper} />;
      case 'exceptions':
        return <ExceptionsView exceptions={exceptions} onOpenResolve={onOpenResolve} />;
      case 'investigator':
        return (
          <InvestigatorView
            opportunities={opportunities}
            selectedOpportunityId={selectedOpportunityId}
            dossier={dossier}
            onOpenDossierModal={() => onOpenDossier(selectedOpportunityId || '')}
          />
        );
      case 'counties':
        return <CountyRadarView countyBoard={countyBoard} loading={countyBoardLoading} />;
      case 'dealroom':
        return (
          <DealRoomView
            opportunities={opportunities}
            onOpenDossier={onOpenDossier}
            onDeliverDeal={onDeliverDeal}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6">
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

      {renderActiveView()}
    </div>
  );
};
