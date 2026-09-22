import React from 'react';
import { Modal } from '../common/Modal';
import { EquityWaterfall } from '../pof/EquityWaterfall';
import { AuthorityBadge } from '../pof/AuthorityBadge';
import { ControlMap } from '../pof/ControlMap';
import { EvidenceViewer } from '../pof/EvidenceViewer';

interface DossierModalProps {
  isOpen: boolean;
  onClose: () => void;
  dossier: any;
  loading: boolean;
}

export const DossierModal: React.FC<DossierModalProps> = ({
  isOpen,
  onClose,
  dossier,
  loading,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Probate Opportunity File (POF): ${dossier?.opportunity.case_number || 'Loading...'}`}
      subtitle={`8-Profile Canonical Dossier · ${dossier?.opportunity.estate_name || ''}`}
      maxWidth="max-w-5xl"
    >
      {loading ? (
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
  );
};
