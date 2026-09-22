import React, { useState } from 'react';
import { OpportunitySummary } from '../types';
import { uiStore } from '../stores/useUiStore';
import { ApiService } from '../services/api';
import { EquityWaterfall } from '../components/pof/EquityWaterfall';
import { AuthorityBadge } from '../components/pof/AuthorityBadge';
import { ControlMap } from '../components/pof/ControlMap';
import { EvidenceViewer } from '../components/pof/EvidenceViewer';

interface InvestigatorViewProps {
  opportunities: OpportunitySummary[];
  selectedOpportunityId: string | null;
  dossier: any;
  onOpenDossierModal: () => void;
}

export const InvestigatorView: React.FC<InvestigatorViewProps> = ({
  opportunities,
  selectedOpportunityId,
  dossier,
  onOpenDossierModal,
}) => {
  const [aiPrompt, setAiPrompt] = useState<string>('');
  const [aiResponse, setAiResponse] = useState<string>('');
  const [aiLoading, setAiLoading] = useState<boolean>(false);

  const handleAIInvestigate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiPrompt.trim()) return;
    setAiLoading(true);
    try {
      const res = await ApiService.investigateAI(aiPrompt, selectedOpportunityId || undefined);
      setAiResponse(res.narrative || res.response || JSON.stringify(res, null, 2));
    } catch (err: any) {
      setAiResponse(`[ERROR] AI Investigator inquiry failed: ${err.message}`);
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Target Selector */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <label htmlFor="target-opportunity-select" className="text-xs font-mono text-slate-400">Target Opportunity:</label>
          <select
            id="target-opportunity-select"
            value={selectedOpportunityId || ''}
            onChange={(e) => uiStore.setSelectedOpportunityId(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none"
          >
            <option value="">Select Opportunity to Investigate...</option>
            {opportunities.map((o) => (
              <option key={o.id} value={o.id}>
                {o.case_number} · {o.decedent || o.estate_name} ({o.county_name || o.county_id})
              </option>
            ))}
          </select>
        </div>

        {selectedOpportunityId && (
          <button
            onClick={onOpenDossierModal}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-mono font-bold transition"
          >
            Open Deep Dossier Modal
          </button>
        )}
      </div>

      {/* POF Render */}
      {dossier ? (
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
        <div className="p-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
          <p className="text-sm font-mono text-slate-400">
            Select an active opportunity above to inspect the canonical 8-Profile Probate Opportunity File (POF).
          </p>
        </div>
      )}

      {/* AI Investigator Live Console */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            AI Lead Investigator & Statutory Assistant
          </h4>
          <p className="text-xs text-slate-400 font-sans">
            Ask questions regarding deed chain integrity, statutory authority (RCW Title 11), or heir consensus
          </p>
        </div>

        <form onSubmit={handleAIInvestigate} className="flex gap-3">
          <input
            type="text"
            placeholder="e.g. Verify RCW 11.68 powers and check if Letters Testamentary grant nonintervention sale authority..."
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={aiLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg font-mono text-xs font-bold transition"
          >
            {aiLoading ? 'Querying...' : 'Investigate'}
          </button>
        </form>

        {aiResponse && (
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 whitespace-pre-wrap">
            {aiResponse}
          </div>
        )}
      </div>
    </div>
  );
};
