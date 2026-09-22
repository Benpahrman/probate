import React from 'react';
import { OpportunitySummary } from '../types';
import { Badge } from '../components/common/Badge';
import { ApiService } from '../services/api';
import { uiStore } from '../stores/useUiStore';

interface DealRoomViewProps {
  opportunities: OpportunitySummary[];
  onOpenDossier: (oppId: string) => void;
  onDeliverDeal: (oppId: string, notes: string) => void;
}

const DELIVERABLE_STAGES = new Set(['READY', 'DELIVERED']);

const isDeliverableDeal = (deal: OpportunitySummary): boolean => {
  return Boolean(deal.is_qc_certified || DELIVERABLE_STAGES.has(deal.workflow_stage));
};

const dispatchCrmDeal = async (
  deal: OpportunitySummary,
  onDeliverDeal: (oppId: string, notes: string) => void
) => {
  try {
    const targetUrl = window.prompt(
      'Enter Partner CRM Webhook URL (e.g. https://httpbin.org/post):',
      'https://httpbin.org/post'
    );
    if (!targetUrl) return;
    const res = await ApiService.exportCrm(deal.id, targetUrl);
    uiStore.addToast({
      type: 'success',
      title: 'CRM Dispatched',
      message: res.message || `Dispatched webhook payload for ${deal.case_number}`,
    });
    onDeliverDeal(deal.id, 'Dispatched to CRM partner webhook');
  } catch (err: any) {
    uiStore.addToast({
      type: 'error',
      title: 'Dispatch Failed',
      message: err.message,
    });
  }
};

interface DealCardProps {
  deal: OpportunitySummary;
  onOpenDossier: (oppId: string) => void;
  onDispatchCrm: (deal: OpportunitySummary) => void;
}

const DealCard: React.FC<DealCardProps> = ({ deal, onOpenDossier, onDispatchCrm }) => {
  const decedentOrEstate = deal.decedent || deal.estate_name;
  const countyDisplay = deal.county_name || deal.county_id;
  const isDelivered = deal.workflow_stage === 'DELIVERED';
  const stageStatusClass = isDelivered ? 'text-emerald-400 font-bold' : 'text-amber-400';

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4 hover:border-emerald-500/40 transition">
      <div className="flex justify-between items-start">
        <div>
          <span className="text-xs font-mono text-indigo-400 font-bold">{deal.case_number}</span>
          <h4 className="text-sm font-bold text-white mt-0.5">{decedentOrEstate}</h4>
          <span className="text-[11px] text-slate-400 font-mono">{countyDisplay}</span>
        </div>
        <Badge type="priority" value={deal.priority} />
      </div>

      <div className="space-y-1 text-xs font-mono text-slate-300 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
        <div className="flex justify-between">
          <span className="text-slate-500">Viability Score:</span>
          <span className="text-emerald-400 font-bold">{deal.score} / 100</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Authority:</span>
          <span className="text-slate-200">{deal.authority_status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Delivery Status:</span>
          <span className={stageStatusClass}>
            {deal.workflow_stage}
          </span>
        </div>
      </div>

      <div className="flex space-x-3">
        <button
          onClick={() => onOpenDossier(deal.id)}
          className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-mono font-bold transition"
        >
          View Dossier
        </button>
        <button
          onClick={() => onDispatchCrm(deal)}
          className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold shadow-lg shadow-emerald-600/20 transition"
        >
          Dispatch to CRM
        </button>
      </div>
    </div>
  );
};

export const DealRoomView: React.FC<DealRoomViewProps> = ({
  opportunities,
  onOpenDossier,
  onDeliverDeal,
}) => {
  const deliverableDeals = opportunities.filter(isDeliverableDeal);

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Certified Wholesaler Deal Delivery Engine
          </h3>
          <p className="text-xs text-slate-400 font-sans">
            Pre-cleared off-market inventory ready for immediate assignment & CRM dispatch
          </p>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {deliverableDeals.map((deal) => (
            <DealCard
              key={deal.id}
              deal={deal}
              onOpenDossier={onOpenDossier}
              onDispatchCrm={(d) => dispatchCrmDeal(d, onDeliverDeal)}
            />
          ))}
          {deliverableDeals.length === 0 && (
            <div className="col-span-2 text-center py-16 text-slate-500 font-mono text-sm">
              No QC-certified deals currently available for delivery. Pass all 6 gates in Pipeline Workbench to certify inventory.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
