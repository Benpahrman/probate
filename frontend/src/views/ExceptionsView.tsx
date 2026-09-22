import React from 'react';
import { ExceptionItem } from '../types';
import { Table, Column } from '../components/common/Table';

interface ExceptionsViewProps {
  exceptions: ExceptionItem[];
  onOpenResolve: (exc: ExceptionItem) => void;
}

export const ExceptionsView: React.FC<ExceptionsViewProps> = ({ exceptions, onOpenResolve }) => {
  const exceptionColumns: Column<ExceptionItem>[] = [
    {
      header: 'Exception ID / Opportunity',
      render: (row) => (
        <div>
          <span className="font-mono font-bold text-slate-200 block">{row.id}</span>
          <span className="text-[10px] font-mono text-indigo-400">{row.opportunity_id}</span>
        </div>
      ),
    },
    {
      header: 'Gate / Failure Reason',
      render: (row) => (
        <div>
          <span className="font-mono font-bold text-amber-400 block">{row.type}</span>
          <span className="text-xs text-slate-400">{row.notes || 'Quarantined for verification'}</span>
        </div>
      ),
    },
    {
      header: 'Urgency',
      render: (row) => (
        <span
          className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
            row.severity === 'CRITICAL'
              ? 'bg-rose-600 text-white animate-pulse'
              : 'bg-amber-600 text-white'
          }`}
        >
          {row.severity}
        </span>
      ),
    },
    {
      header: 'SLA Remaining',
      render: (row) => (
        <span className="font-mono text-xs font-bold text-slate-300">
          {row.sla_hours_remaining ? `${row.sla_hours_remaining}h : 00m` : '24h : 00m'}
        </span>
      ),
    },
    {
      header: 'Status',
      render: (row) => (
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-mono ${
            row.status === 'RESOLVED'
              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
              : 'bg-amber-950 text-amber-400 border border-amber-800'
          }`}
        >
          {row.status}
        </span>
      ),
    },
    {
      header: 'Action',
      className: 'text-right',
      render: (row) => (
        <button
          disabled={row.status === 'RESOLVED'}
          onClick={() => onOpenResolve(row)}
          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded font-mono text-xs font-bold transition"
        >
          {row.status === 'RESOLVED' ? 'Resolved' : 'Resolve Triage'}
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Quarantined Exception Queue
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              Records Flagged by Gates 1–6 Requiring Human Review & Remediation
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">Active Exceptions: {exceptions.length}</span>
        </div>

        <Table
          columns={exceptionColumns}
          data={exceptions}
          keyField="id"
          emptyMessage="All quality gates passing cleanly. Zero quarantined records."
        />
      </div>
    </div>
  );
};
