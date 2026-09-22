import React from 'react';
import { useUiStore, uiStore } from '../../stores/useUiStore';

const TAB_TITLES: Record<string, string> = {
  pipeline: '14-Stage Opportunity Pipeline Workbench',
  county: 'Municipal Court Scraper & Intake Hub',
  exceptions: 'Quarantined Tasks & Exceptions Triage',
  investigator: 'Probate Opportunity File (POF) Investigator',
  counties: 'Washington Jurisdictional Radar',
  dealroom: 'Certified Wholesaler Deal Room & CRM Dispatch',
};

interface HeaderProps {
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh }) => {
  const { activeTab, selectedCounty } = useUiStore();

  const handleRefresh = () => {
    onRefresh();
    uiStore.addToast({
      type: 'info',
      title: 'State Synchronized',
      message: 'Synchronized live state from Platform API.',
    });
  };

  return (
    <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-slate-900/50 backdrop-blur shrink-0">
      <h2 className="text-base font-bold tracking-tight text-white font-mono">
        {TAB_TITLES[activeTab] || 'Decision Intelligence Platform'}
      </h2>

      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
          <label htmlFor="territory-select" className="text-[11px] font-mono text-slate-400">
            Territory:
          </label>
          <select
            id="territory-select"
            value={selectedCounty}
            onChange={(e) => uiStore.setSelectedCounty(e.target.value)}
            className="bg-transparent text-xs font-mono text-white focus:outline-none cursor-pointer"
          >
            <option value="ALL">All Washington Territories</option>
            <option value="Thurston">Thurston County (53067)</option>
            <option value="Pierce">Pierce County (53053)</option>
            <option value="King">King County (53033)</option>
            <option value="Snohomish">Snohomish County (53061)</option>
          </select>
        </div>

        <button
          onClick={handleRefresh}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 active:scale-95 transition text-xs font-semibold rounded-lg border border-slate-700 flex items-center space-x-1.5"
        >
          <span>⟳</span>
          <span>Refresh Live State</span>
        </button>
      </div>
    </header>
  );
};
