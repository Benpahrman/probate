import React from 'react';
import { QualityControlAuditSummary } from '../../types';
import { Modal } from '../common/Modal';
import { Badge } from '../common/Badge';

interface QcAuditModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: QualityControlAuditSummary | null;
}

export const QcAuditModal: React.FC<QcAuditModalProps> = ({ isOpen, onClose, summary }) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Quality Control Audit Report (6 Deterministic Gates)"
      subtitle={`Audit results for Opportunity ${summary?.opportunity_id}`}
    >
      {summary && (
        <div className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-slate-950 rounded-lg border border-slate-800">
            <div>
              <span className="text-xs font-mono text-slate-400 block">Overall Certification Status:</span>
              <span
                className={`text-base font-mono font-bold ${
                  summary.is_fully_certified ? 'text-emerald-400' : 'text-amber-400'
                }`}
              >
                {summary.is_fully_certified ? '✓ FULLY CERTIFIED' : '⚠ GATE INTERCEPTED'}
              </span>
            </div>
            <Badge
              type="gate"
              value={summary.is_fully_certified ? 'QC_CERTIFIED' : 'GATE_FAILED'}
            />
          </div>

          <div className="space-y-2">
            <h5 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
              Gate-by-Gate Verification Matrix:
            </h5>
            <div className="space-y-2">
              {summary.gate_results.map((g) => (
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
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-mono"
            >
              Close Audit Report
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
};
