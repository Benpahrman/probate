import React from 'react';
import { useUiStore, uiStore, WorkspaceTab } from '../../stores/useUiStore';
import { useWebSocket } from '../../hooks/useWebSocket';

interface SidebarProps {
  opportunitiesCount: number;
  casesCount: number;
  openExceptionsCount: number;
}

interface NavItemConfig {
  id: WorkspaceTab;
  icon: string;
  label: string;
  countBadge?: number | string;
  isPulseBadge?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  opportunitiesCount,
  casesCount,
  openExceptionsCount,
}) => {
  const { activeTab } = useUiStore();
  const { isConnected } = useWebSocket();

  const coreTabs: NavItemConfig[] = [
    { id: 'pipeline', icon: '📊', label: '1. Pipeline Workbench', countBadge: opportunitiesCount },
    { id: 'county', icon: '🏛️', label: '2. County Intake Hub', countBadge: casesCount },
    {
      id: 'exceptions',
      icon: '⚠️',
      label: '3. Tasks & Exceptions',
      countBadge: openExceptionsCount > 0 ? openExceptionsCount : undefined,
      isPulseBadge: openExceptionsCount > 0,
    },
    { id: 'investigator', icon: '🔍', label: '4. Property Investigator', countBadge: 'POF' },
  ];

  const marketTabs: NavItemConfig[] = [
    { id: 'counties', icon: '🗺️', label: '5. County Radar' },
    { id: 'dealroom', icon: '🤝', label: '6. Wholesaler Deal Room' },
  ];

  const renderNavButton = (tab: NavItemConfig) => {
    const isActive = activeTab === tab.id;
    return (
      <button
        key={tab.id}
        onClick={() => uiStore.setActiveTab(tab.id)}
        className={`w-full flex items-center justify-between px-3.5 py-2.5 text-xs font-semibold rounded-lg transition ${
          isActive
            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
            : 'text-slate-400 hover:bg-slate-800 hover:text-white'
        }`}
      >
        <div className="flex items-center space-x-2.5">
          <span>{tab.icon}</span>
          <span>{tab.label}</span>
        </div>
        {tab.countBadge !== undefined && (
          tab.isPulseBadge ? (
            <span className="text-[10px] font-mono font-black bg-rose-600 text-white px-1.5 py-0.5 rounded-full animate-pulse">
              {tab.countBadge}
            </span>
          ) : (
            <span className={`text-[10px] font-mono ${typeof tab.countBadge === 'string' ? 'text-indigo-300' : 'opacity-80'}`}>
              {tab.countBadge}
            </span>
          )
        )}
      </button>
    );
  };

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between select-none">
      <div>
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-black tracking-widest text-indigo-400">GIENI OS</span>
            <span className="text-[10px] bg-indigo-900/80 text-indigo-300 font-mono px-1.5 py-0.5 rounded border border-indigo-700">
              PROD
            </span>
          </div>
          <p className="text-[11px] text-slate-500 tracking-wider mt-1 font-mono">
            DECISION INTELLIGENCE v2.0
          </p>
        </div>

        <nav className="p-4 space-y-1.5">
          <div className="px-2 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono">
            Workspaces
          </div>
          {coreTabs.map(renderNavButton)}

          <div className="pt-4 px-2 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono">
            Market Intelligence
          </div>
          {marketTabs.map(renderNavButton)}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 bg-slate-950/40">
        <div className="flex items-center space-x-2.5">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
            }`}
          />
          <span className="font-semibold text-slate-300 font-mono">
            {isConnected ? 'Telemetry Online' : 'Connecting WS'}
          </span>
        </div>
        <div className="text-[10px] text-slate-500 mt-1 font-mono">
          Direct Live I/O · Washington Title 11
        </div>
      </div>
    </aside>
  );
};
