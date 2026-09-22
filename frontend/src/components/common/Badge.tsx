import React from 'react';

interface BadgeProps {
  type: 'priority' | 'authority' | 'gate' | 'stage';
  value: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ type, value, className = '' }) => {
  const norm = (value || '').toUpperCase();

  if (type === 'priority') {
    if (norm === 'PRIORITY_A' || norm === 'A' || norm === 'HIGH') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] uppercase tracking-wider bg-rose-600 text-white font-black animate-pulse shadow-sm shadow-rose-900/50 ${className}`}>
          ● Priority A
        </span>
      );
    }
    if (norm === 'PRIORITY_B' || norm === 'B' || norm === 'MEDIUM') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] uppercase tracking-wider bg-blue-600 text-white font-semibold ${className}`}>
          Priority B
        </span>
      );
    }
    if (norm === 'PRIORITY_C' || norm === 'C' || norm === 'LOW') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] uppercase tracking-wider bg-amber-600 text-white font-medium ${className}`}>
          Priority C
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] uppercase tracking-wider bg-slate-800 text-slate-400 font-normal border border-slate-700 ${className}`}>
        Disqualified
      </span>
    );
  }

  if (type === 'authority') {
    if (norm.includes('TIER_1') || norm.includes('CONFIRMED')) {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono tracking-tight bg-emerald-950 text-emerald-400 border border-emerald-800 ${className}`}>
          ✓ Tier 1 (Letters Confirmed)
        </span>
      );
    }
    if (norm.includes('TIER_2') || norm.includes('LIKELY')) {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono tracking-tight bg-blue-950 text-blue-400 border border-blue-800 ${className}`}>
          Tier 2 (Likely Sole Heir)
        </span>
      );
    }
    if (norm.includes('TIER_3') || norm.includes('STAKEHOLDER')) {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono tracking-tight bg-amber-950 text-amber-400 border border-amber-800 ${className}`}>
          Tier 3 (Multi-Heir Consensus)
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono tracking-tight bg-rose-950 text-rose-400 border border-rose-800 ${className}`}>
        ✕ Tier 4 (Unresolved - Locked)
      </span>
    );
  }

  if (type === 'gate') {
    if (norm === 'QC_CERTIFIED' || norm === 'CERTIFIED' || norm === 'READY' || norm === 'PASSED') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] uppercase tracking-wider bg-emerald-600 text-white font-bold shadow-sm shadow-emerald-900/40 ${className}`}>
          ✓ QC Certified
        </span>
      );
    }
    if (norm === 'GATE_FAILED' || norm === 'FAILED' || norm === 'EXCEPTION') {
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] uppercase tracking-wider bg-amber-500 text-slate-950 font-bold ${className}`}>
          ⚠ Gate Intercept
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700 ${className}`}>
        Pending QC
      </span>
    );
  }

  // Stage Badge
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700 ${className}`}>
      {value}
    </span>
  );
};
