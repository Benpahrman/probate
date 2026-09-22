import React from 'react';
import { OpportunitySummary, QualityControlAuditSummary, ExceptionItem, FullPOFDossier } from '../../types';
import { QcAuditModal } from '../modals/QcAuditModal';
import { TransitionModal } from '../modals/TransitionModal';
import { DossierModal } from '../modals/DossierModal';
import { Modal } from '../common/Modal';
import { ExceptionResolve } from '../forms/ExceptionResolve';

interface AppModalsProps {
  qcModalOpen: boolean;
  onCloseQcModal: () => void;
  activeQcSummary: QualityControlAuditSummary | null;

  transitionModalOpen: boolean;
  onCloseTransitionModal: () => void;
  targetOppForTransition: OpportunitySummary | null;
  onAdvanceStage: (oppId: string, targetStage: string) => Promise<boolean>;

  resolveModalOpen: boolean;
  onCloseResolveModal: () => void;
  selectedException: ExceptionItem | null;
  onResolveException: (exceptionId: string, notes: string) => Promise<boolean>;
  onReAuditOpportunity: (opp: OpportunitySummary) => void;
  opportunities: OpportunitySummary[];

  dossierModalOpen: boolean;
  onCloseDossierModal: () => void;
  dossier: FullPOFDossier | null;
  dossierLoading: boolean;
}

export const AppModals: React.FC<AppModalsProps> = ({
  qcModalOpen,
  onCloseQcModal,
  activeQcSummary,
  transitionModalOpen,
  onCloseTransitionModal,
  targetOppForTransition,
  onAdvanceStage,
  resolveModalOpen,
  onCloseResolveModal,
  selectedException,
  onResolveException,
  onReAuditOpportunity,
  opportunities,
  dossierModalOpen,
  onCloseDossierModal,
  dossier,
  dossierLoading,
}) => {
  return (
    <>
      <QcAuditModal
        isOpen={qcModalOpen}
        onClose={onCloseQcModal}
        summary={activeQcSummary}
      />

      <TransitionModal
        isOpen={transitionModalOpen}
        onClose={onCloseTransitionModal}
        targetOpp={targetOppForTransition}
        onCommit={onAdvanceStage}
      />

      <Modal
        isOpen={resolveModalOpen}
        onClose={onCloseResolveModal}
        title="Resolve Quarantined Exception"
        subtitle={`Correction Protocol for Exception ${selectedException?.id}`}
      >
        {selectedException && (
          <ExceptionResolve
            exception={selectedException}
            onCommit={onResolveException}
            onCancel={onCloseResolveModal}
            onReAudit={(oppId) => {
              onCloseResolveModal();
              const opp = opportunities.find((o) => o.id === oppId);
              if (opp) onReAuditOpportunity(opp);
            }}
          />
        )}
      </Modal>

      <DossierModal
        isOpen={dossierModalOpen}
        onClose={onCloseDossierModal}
        dossier={dossier}
        loading={dossierLoading}
      />
    </>
  );
};
