import React, { useState, useMemo } from 'react';
import { OpportunitySummary, LifecycleStage } from '../types';
import { Badge } from '../components/common/Badge';
import { Table, Column } from '../components/common/Table';
import { uiStore } from '../stores/useUiStore';

interface PipelineViewProps {
  opportunities: OpportunitySummary[];
  loading: boolean;
  searchQuery: string;
  stageFilter: string;
  onAuditQC: (opp: OpportunitySummary) => void;
  onOpenTransition: (opp: OpportunitySummary) => void;
  onOpenDossier: (oppId: string) => void;
}

const KANBAN_STAGES: LifecycleStage[] = [
  'DISCOVERED',
  'PROPERTY_IDENTIFIED',
  'OWNERSHIP_RESOLVED',
  'CONTROL_MAPPED',
  'AUTHORITY_RESOLVED',
  'SCORED',
  'QC_CERTIFIED',
  'DELIVERED',
  'CONTACTED',
  'APPOINTMENT',
  'OFFER',
  'CONTRACT',
  'CLOSED_WON',
  'ARCHIVED',
];

const STAGE_NORMALIZATION_MAP: Record<string, LifecycleStage> = {
  NEW: 'DISCOVERED',
  DISCOVERED: 'DISCOVERED',
  QC: 'SCORED',
  READY: 'QC_CERTIFIED',
  EXCEPTION: 'SCORED',
  DELIVERED: 'DELIVERED',
  CONTACTED: 'CONTACTED',
  APPOINTMENT: 'APPOINTMENT',
  OFFER: 'OFFER',
  CONTRACT: 'CONTRACT',
  CLOSED_WON: 'CLOSED_WON',
  CLOSED_LOST: 'CLOSED_LOST',
  ARCHIVED: 'ARCHIVED',
};

const normalizeStage = (opp: OpportunitySummary): LifecycleStage => {
  if (opp.lifecycle_stage) return opp.lifecycle_stage;
  const wf = (opp.workflow_stage || '').toUpperCase();
  return STAGE_NORMALIZATION_MAP[wf] || 'DISCOVERED';
};

const matchesSearch = (opp: OpportunitySummary, query: string): boolean => {
  if (!query) return true;
  const q = query.toLowerCase();
  const caseNum = (opp.case_number || '').toLowerCase();
  const decedent = (opp.decedent || opp.estate_name || '').toLowerCase();
  const county = (opp.county_name || opp.county_id || '').toLowerCase();
  return caseNum.includes(q) || decedent.includes(q) || county.includes(q);
};

export const PipelineView: React.FC<PipelineViewProps> = ({
  opportunities,
  loading,
  searchQuery,
  stageFilter,
  onAuditQC,
  onOpenTransition,
  onOpenDossier,
}) => {
  const [pipelineViewMode, setPipelineViewMode] = useState<'table' | 'kanban'>('table');
  const [minEquityFilter, setMinEquityFilter] = useState<number>(30);

  const filteredOpps = useMemo(() => {
    return opportunities.filter((opp) => matchesSearch(opp, searchQuery));
  }, [opportunities, searchQuery]);

  const oppColumns: Column<OpportunitySummary>[] = [
    {
      header: 'Case # / Decedent',
      render: (row) => (
        <div>
          <span className="font-mono font-bold text-indigo-400 block">{row.case_number}</span>
          <span className="text-slate-300 truncate max-w-[200px] block">{row.decedent || row.estate_name}</span>
          <span className="text-[10px] text-slate-500 font-mono">{row.county_name || row.county_id}</span>
        </div>
      ),
    },
    {
      header: 'Stage',
      render: (row) => <Badge type="stage" value={row.workflow_stage} />,
    },
    {
      header: 'Score / DFS',
      render: (row) => (
        <div className="font-mono">
          <span className="font-bold text-white">{row.score}</span>
          <span className="text-slate-500 text-[10px] block">DFS: -{Math.max(10, 100 - row.score)}</span>
        </div>
      ),
    },
    {
      header: 'Priority',
      render: (row) => <Badge type="priority" value={row.priority} />,
    },
    {
      header: 'Authority Scope',
      render: (row) => <Badge type="authority" value={row.authority_status} />,
    },
    {
      header: 'QC Certification',
      render: (row) => (
        <Badge
          type="gate"
          value={row.is_qc_certified || row.workflow_stage === 'READY' || row.workflow_stage === 'DELIVERED' ? 'QC_CERTIFIED' : 'PENDING'}
        />
      ),
    },
    {
      header: 'Actions',
      className: 'text-right',
      render: (row) => (
        <div className="flex items-center justify-end space-x-2">
          <button
            onClick={() => onAuditQC(row)}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-mono text-[11px] border border-slate-700 active:scale-95 transition"
            title="Audit against 6 deterministic quality gates"
          >
            Audit 6 Gates
          </button>
          <button
            onClick={() => onOpenTransition(row)}
            className="px-2.5 py-1 bg-indigo-900/50 hover:bg-indigo-800 text-indigo-200 rounded font-mono text-[11px] border border-indigo-700/60 active:scale-95 transition"
            title="Advance FSM lifecycle stage"
          >
            Advance
          </button>
          <button
            onClick={() => onOpenDossier(row.id)}
            className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-mono text-[11px] shadow-sm shadow-indigo-600/30 active:scale-95 transition"
          >
            Dossier &rarr;
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Filter & View Bar */}
      <div className="flex items-center justify-between gap-4 p-4 bg-slate-900 border border-slate-800 rounded-xl">
        <div className="flex items-center space-x-4 flex-1">
          <div className="relative flex-1 max-w-sm">
            <input
              type="text"
              placeholder="Search case #, decedent, county..."
              value={searchQuery}
              onChange={(e) => uiStore.setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center space-x-2">
            <label htmlFor="stage-filter-select" className="text-xs font-mono text-slate-400">Stage:</label>
            <select
              id="stage-filter-select"
              value={stageFilter}
              onChange={(e) => uiStore.setStageFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono focus:outline-none"
            >
              <option value="ALL">All Stages</option>
              <option value="SCORED">SCORED</option>
              <option value="QC">QC</option>
              <option value="READY">READY</option>
              <option value="DELIVERED">DELIVERED</option>
              <option value="EXCEPTION">EXCEPTION</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label htmlFor="min-equity-slider" className="text-xs font-mono text-slate-400">Min Equity:</label>
            <input
              id="min-equity-slider"
              type="range"
              min={30}
              max={100}
              value={minEquityFilter}
              onChange={(e) => setMinEquityFilter(Number(e.target.value))}
              className="w-20 h-1 bg-slate-800 rounded appearance-none cursor-pointer accent-indigo-500"
            />
            <span className="text-xs font-mono text-slate-300 font-bold">{minEquityFilter}%</span>
          </div>
        </div>

        <div className="flex items-center space-x-1 bg-slate-950 p-1 border border-slate-800 rounded-lg">
          <button
            onClick={() => setPipelineViewMode('table')}
            className={`px-3 py-1 text-xs font-mono rounded ${
              pipelineViewMode === 'table' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Dense Table
          </button>
          <button
            onClick={() => setPipelineViewMode('kanban')}
            className={`px-3 py-1 text-xs font-mono rounded ${
              pipelineViewMode === 'kanban' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            14-Stage Kanban
          </button>
        </div>
      </div>

      {pipelineViewMode === 'table' ? (
        loading ? (
          <div className="p-12 text-center font-mono text-slate-400">Loading live opportunities...</div>
        ) : (
          <Table
            columns={oppColumns}
            data={filteredOpps}
            keyField="id"
            emptyMessage="No opportunities found matching search criteria."
          />
        )
      ) : (
        <div className="flex space-x-4 overflow-x-auto pb-4">
          {KANBAN_STAGES.map((stage) => {
            const stageOpps = filteredOpps.filter((o) => normalizeStage(o) === stage);
            return (
              <div
                key={stage}
                className="w-72 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col shrink-0 min-h-[500px]"
              >
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                  <span className="text-xs font-mono font-bold text-slate-200 truncate">{stage}</span>
                  <span className="text-[10px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
                    {stageOpps.length}
                  </span>
                </div>
                <div className="space-y-3 flex-1 overflow-y-auto">
                  {stageOpps.map((opp) => (
                    <div
                      key={opp.id}
                      className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2 hover:border-indigo-500/50 transition cursor-pointer"
                      onClick={() => onOpenDossier(opp.id)}
                    >
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-mono font-bold text-indigo-400">{opp.case_number}</span>
                        <Badge type="priority" value={opp.priority} />
                      </div>
                      <p className="text-xs text-slate-300 font-semibold truncate">{opp.decedent || opp.estate_name}</p>
                      <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-900">
                        <span>Score: {opp.score}</span>
                        <span>{opp.county_name || opp.county_id}</span>
                      </div>
                    </div>
                  ))}
                  {stageOpps.length === 0 && (
                    <div className="text-center text-[11px] text-slate-600 font-mono py-8">No records</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
