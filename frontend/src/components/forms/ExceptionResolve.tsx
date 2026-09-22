import React, { useState } from 'react';
import { ExceptionItem } from '../../types';

interface ExceptionResolveProps {
  exception: ExceptionItem;
  onCommit: (id: string, notes: string) => Promise<boolean>;
  onCancel: () => void;
  onReAudit?: (opportunityId: string) => void;
}

const getInitialCorrectionType = (type: string) => {
  if (type.includes('GATE_2')) return 'APN_OVERRIDE';
  if (type.includes('GATE_4')) return 'LETTERS_CLASSIFICATION';
  return 'CONTACT_REPLACEMENT';
};

const buildAuditDetails = (
  correctionType: string,
  apnOverride: string,
  lettersStatus: string,
  contactLine: string,
  notes: string
): string => {
  const prefix = `[Corrective Action: ${correctionType}] `;
  const detailMap: Record<string, string> = {
    APN_OVERRIDE: `APN Override committed: ${apnOverride}. `,
    LETTERS_CLASSIFICATION: `Letters classified as: ${lettersStatus}. `,
    CONTACT_REPLACEMENT: `Direct fiduciary line updated: ${contactLine}. `,
  };
  const body = detailMap[correctionType] || '';
  const noteSuffix = notes ? `Operator Notes: ${notes}` : 'Audited and verified against primary court filings.';
  return `${prefix}${body}${noteSuffix}`;
};

const ExceptionDetailsSummary: React.FC<{ exception: ExceptionItem }> = ({ exception }) => (
  <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 space-y-2 text-xs font-mono">
    <div className="flex justify-between">
      <span className="text-slate-400">Exception ID:</span>
      <span className="text-slate-200">{exception.id}</span>
    </div>
    <div className="flex justify-between">
      <span className="text-slate-400">Target Opportunity:</span>
      <span className="text-indigo-400 font-bold">{exception.opportunity_id}</span>
    </div>
    <div className="flex justify-between">
      <span className="text-slate-400">Gate Failure Classification:</span>
      <span className="text-amber-400 font-bold">{exception.type}</span>
    </div>
    <div className="flex justify-between">
      <span className="text-slate-400">Current Notes:</span>
      <span className="text-slate-300">{exception.notes || 'Awaiting operator audit triage'}</span>
    </div>
  </div>
);

export const ExceptionResolve: React.FC<ExceptionResolveProps> = ({
  exception,
  onCommit,
  onCancel,
  onReAudit,
}) => {
  const [correctionType, setCorrectionType] = useState<string>(() => getInitialCorrectionType(exception.type));
  const [apnOverride, setApnOverride] = useState<string>('');
  const [lettersStatus, setLettersStatus] = useState<string>('CONFIRMED_NONINTERVENTION');
  const [contactLine, setContactLine] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    const auditDetails = buildAuditDetails(correctionType, apnOverride, lettersStatus, contactLine, notes);
    const ok = await onCommit(exception.id, auditDetails);
    setSubmitting(false);

    if (ok && onReAudit) {
      onReAudit(exception.opportunity_id);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ExceptionDetailsSummary exception={exception} />

      <div className="space-y-3">
        <div>
          <label htmlFor="correction-protocol-select" className="block text-xs font-mono text-slate-300 mb-1">
            Correction Protocol
          </label>
          <select
            id="correction-protocol-select"
            value={correctionType}
            onChange={(e) => setCorrectionType(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
          >
            <option value="APN_OVERRIDE">Gate 2 Correction: Manual APN & Parcel Card Override</option>
            <option value="LETTERS_CLASSIFICATION">Gate 4 Correction: Letters Testamentary Classification</option>
            <option value="CONTACT_REPLACEMENT">Gate 5 Correction: Fiduciary Direct Contact Line Update</option>
            <option value="MANUAL_AUDIT">General Manual Review Verification</option>
          </select>
        </div>

        {correctionType === 'APN_OVERRIDE' && (
          <div>
            <label htmlFor="apn-override-input" className="block text-xs font-mono text-slate-300 mb-1">
              Corrected Assessor Parcel Number (APN)
            </label>
            <input
              id="apn-override-input"
              type="text"
              required
              placeholder="e.g. 041-280-001-002"
              value={apnOverride}
              onChange={(e) => setApnOverride(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>
        )}

        {correctionType === 'LETTERS_CLASSIFICATION' && (
          <div>
            <label htmlFor="letters-classification-select" className="block text-xs font-mono text-slate-300 mb-1">
              Letters Authority Classification
            </label>
            <select
              id="letters-classification-select"
              value={lettersStatus}
              onChange={(e) => setLettersStatus(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            >
              <option value="CONFIRMED_NONINTERVENTION">RCW 11.68 Confirmed (Nonintervention Powers)</option>
              <option value="LIMITED_WITH_ORDER">RCW 11.56 Order of Sale Confirmed</option>
              <option value="SOLE_HEIR_AFFIDAVIT">RCW 11.62 Small Estate Affidavit Verified</option>
            </select>
          </div>
        )}

        {correctionType === 'CONTACT_REPLACEMENT' && (
          <div>
            <label htmlFor="contact-line-input" className="block text-xs font-mono text-slate-300 mb-1">
              Verified Fiduciary Direct Line
            </label>
            <input
              id="contact-line-input"
              type="text"
              required
              placeholder="+1 (360) 555-0192"
              value={contactLine}
              onChange={(e) => setContactLine(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>
        )}

        <div>
          <label htmlFor="audit-notes-textarea" className="block text-xs font-mono text-slate-300 mb-1">
            Audit Trail Notes (Required)
          </label>
          <textarea
            id="audit-notes-textarea"
            rows={3}
            required
            placeholder="Document court docket reference and reason for correction..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-sans focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-3 border-t border-slate-800">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-mono transition"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold shadow-lg shadow-emerald-600/20 transition disabled:opacity-50"
        >
          {submitting ? 'Committing Triage...' : 'Commit Resolution & Re-Audit 6 Gates'}
        </button>
      </div>
    </form>
  );
};
