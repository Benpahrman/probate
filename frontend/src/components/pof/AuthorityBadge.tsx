import React from 'react';
import { AuthorityProfile } from '../../types';

interface AuthorityBadgeProps {
  authority: AuthorityProfile;
}

const TierBadge: React.FC<{ tier?: string }> = ({ tier = 'TIER_1_CONFIRMED' }) => {
  const isTier1 = tier.includes('TIER_1') || tier.includes('CONFIRMED');
  const colorClasses = isTier1
    ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
    : 'bg-amber-950 text-amber-300 border-amber-700';
  return (
    <span className={`px-3 py-1 rounded text-xs font-mono font-bold tracking-wide border ${colorClasses}`}>
      {tier}
    </span>
  );
};

const CourtConfirmationStatus: React.FC<{ required: boolean }> = ({ required }) => {
  const textClass = required ? 'text-amber-400' : 'text-emerald-400';
  const label = required ? 'Required (Full Hearing)' : 'Waived by Statute';
  return <span className={textClass}>{label}</span>;
};

const PsaSignatoryBadge: React.FC<{ canSign: boolean }> = ({ canSign }) => {
  const badgeClasses = canSign
    ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
    : 'bg-rose-950 text-rose-400 border-rose-800';
  return (
    <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${badgeClasses}`}>
      {canSign ? 'UNLOCKED / EXCLUSIVE' : 'LOCKED'}
    </span>
  );
};

export const AuthorityBadge: React.FC<AuthorityBadgeProps> = ({ authority }) => {
  const statutoryBasis = authority.statutory_basis || 'RCW 11.68.090';
  const oversightModel = authority.court_oversight_model || 'Nonintervention Powers';
  const powerScope =
    authority.statutory_power_scope ||
    'Full independent power to convey, sell, and encumber real estate without court approval.';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            4. Authority Resolution Engine (ARE)
          </h4>
          <p className="text-xs text-slate-400 font-sans">Washington RCW Title 11 Probate Power Scope</p>
        </div>
        <div>
          <TierBadge tier={authority.authority_tier} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="space-y-2 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
          <div className="flex justify-between">
            <span className="text-slate-400">Statutory Basis:</span>
            <span className="text-indigo-300 font-bold">{statutoryBasis}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Court Oversight:</span>
            <span className="text-slate-200">{oversightModel}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Court Confirmation:</span>
            <CourtConfirmationStatus required={!!authority.court_confirmation_required} />
          </div>
        </div>

        <div className="space-y-2 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
          <div className="flex justify-between items-center">
            <span className="text-slate-400">PSA Signatory Authority:</span>
            <PsaSignatoryBadge canSign={!!authority.can_execute_psa} />
          </div>
          <div className="text-[11px] text-slate-400 font-sans mt-2">
            <span className="font-semibold text-slate-300">Powers Scope:</span> {powerScope}
          </div>
        </div>
      </div>
    </div>
  );
};
