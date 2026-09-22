import React, { useState, useEffect } from 'react';
import { OpportunitySummary } from '../../types';
import { Modal } from '../common/Modal';
import { uiStore } from '../../stores/useUiStore';

interface TransitionModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetOpp: OpportunitySummary | null;
  onCommit: (oppId: string, targetStage: string, notes: string) => Promise<boolean>;
}

export const TransitionModal: React.FC<TransitionModalProps> = ({
  isOpen,
  onClose,
  targetOpp,
  onCommit,
}) => {
  const [selectedTargetStage, setSelectedTargetStage] = useState<string>('QC');
  const [transitionNotes, setTransitionNotes] = useState<string>('');

  useEffect(() => {
    if (targetOpp) {
      setSelectedTargetStage(targetOpp.is_qc_certified ? 'DELIVERED' : 'QC');
      setTransitionNotes('');
    }
  }, [targetOpp]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetOpp) return;

    if (selectedTargetStage === 'DELIVERED' && !targetOpp.is_qc_certified) {
      uiStore.addToast({
        type: 'error',
        title: 'Compliance Intercept',
        message:
          'Strict Enforcement: Cannot transition to DELIVERED without passing all 6 Quality Gates (is_qc_certified === true).',
      });
      return;
    }

    const success = await onCommit(targetOpp.id, selectedTargetStage, transitionNotes);
    if (success) {
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Advance FSM Lifecycle Stage"
      subtitle={`Validate transition for ${targetOpp?.case_number}`}
      maxWidth="max-w-md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="target-stage-select" className="block text-xs font-mono text-slate-300 mb-1">
            Target Lifecycle Stage
          </label>
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
          <label htmlFor="transition-audit-notes" className="block text-xs font-mono text-slate-300 mb-1">
            Operator Notes
          </label>
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
            onClick={onClose}
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
  );
};
