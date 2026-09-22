import React from 'react';
import { ContactSummary, RiskProfile, RecommendedAction } from '../../types';

interface ControlMapProps {
  contact: ContactSummary;
  risk: RiskProfile;
  action: RecommendedAction;
}

export const ControlMap: React.FC<ControlMapProps> = ({ contact, risk, action }) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* 3. Control Intelligence */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
        <div className="border-b border-slate-800 pb-2">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
            3. Control Intelligence (CIE)
          </h4>
          <p className="text-[11px] text-slate-400 font-sans">Primary Fiduciary & Signatory Contact</p>
        </div>

        <div className="space-y-2 text-xs font-mono">
          <div className="flex justify-between">
            <span className="text-slate-400">Target Decision-Maker:</span>
            <span className="text-white font-bold">{contact.target_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Relationship:</span>
            <span className="text-slate-300">{contact.relationship}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Primary Phone:</span>
            <span className="text-emerald-400 font-bold">{contact.primary_phone || 'Unverified'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Line Type / Carrier:</span>
            <span className="text-slate-300">{contact.line_type || 'Active Wireless'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Skip Trace Status:</span>
            <span className="text-indigo-400 font-bold">{contact.skip_trace_status}</span>
          </div>
        </div>
      </div>

      {/* 5 & 6. Risk Profile & Recommended Actions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
        <div className="border-b border-slate-800 pb-2">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
            5 & 6. Risk & Strategic Directives
          </h4>
          <p className="text-[11px] text-slate-400 font-sans">Acquisition Framing & Execution Directives</p>
        </div>

        <div className="space-y-2 text-xs font-mono">
          <div className="flex justify-between">
            <span className="text-slate-400">Risk Classification:</span>
            <span className="text-emerald-400 font-bold">{risk.overall_deal_risk_classification || 'LOW_RISK'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Foreclosure Risk:</span>
            <span className="text-slate-300">{risk.foreclosure_acceleration_risk || 'None Detected'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Recommended Channel:</span>
            <span className="text-indigo-300 font-bold">{action.first_touch_channel || 'Priority Direct Call'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Transaction Strategy:</span>
            <span className="text-slate-200">{action.transaction_strategy || 'Direct Personal Representative PSA'}</span>
          </div>
          <div className="p-2 bg-slate-950/80 rounded border border-slate-800 text-[11px] font-sans text-slate-300 italic mt-2">
            "{action.conversational_framing_script || 'Empathy-first estate assistance: As-is closing with full probate fee coverage.'}"
          </div>
        </div>
      </div>
    </div>
  );
};
