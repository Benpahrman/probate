import React from 'react';
import { ScraperTrigger } from '../components/forms/ScraperTrigger';
import { Table, Column } from '../components/common/Table';

interface CasesViewProps {
  cases: any[];
  onTriggerScraper: (inputs: any) => Promise<any>;
}

export const CasesView: React.FC<CasesViewProps> = ({ cases, onTriggerScraper }) => {
  const caseColumns: Column<any>[] = [
    {
      header: 'Case Number',
      accessor: 'case_number',
      render: (row) => <span className="font-mono font-bold text-indigo-400">{row.case_number}</span>,
    },
    { header: 'County ID', accessor: 'county_id' },
    { header: 'Decedent / Estate', accessor: 'decedent' },
    { header: 'Filing Date', accessor: 'filing_date' },
    {
      header: 'Status',
      render: (row) => (
        <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">
          {row.status}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <ScraperTrigger onTrigger={onTriggerScraper} />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Ingested Municipal Dockets
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              Washington Superior Court Filings Indexed Live into Database
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">Total Cases: {cases.length}</span>
        </div>

        <Table
          columns={caseColumns}
          data={cases}
          keyField="id"
          emptyMessage="No municipal cases recorded yet. Launch the headless scraper above."
        />
      </div>
    </div>
  );
};
