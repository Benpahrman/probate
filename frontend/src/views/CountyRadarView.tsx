import React from 'react';

export interface CountyBoardItem {
  county_id?: string;
  name: string;
  state?: string;
  tier?: number;
  court_portal?: string;
  status?: string;
  cases_count?: number;
  opportunities_count?: number;
  expansion_score?: number;
  median_home_price?: number;
  conversion_rate?: number | null;
  recommendation?: string;
}

interface CountyRadarViewProps {
  countyBoard: CountyBoardItem[] | any[];
  loading: boolean;
}

const formatPrice = (price?: number | null): string =>
  price ? `$${price.toLocaleString()}` : 'N/A';

const formatConversion = (rate?: number | null): string =>
  rate !== null && rate !== undefined ? `${rate}%` : 'N/A';

const getStatusBadgeClass = (status: string): string =>
  status === 'ACTIVE'
    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
    : 'bg-amber-950 text-amber-400 border border-amber-800';

interface CountyCardProps {
  county: CountyBoardItem;
}

const CountyCard: React.FC<CountyCardProps> = ({ county }) => {
  const status = county.status || 'ACTIVE';
  const state = county.state || 'WA';
  const tier = county.tier || 1;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 hover:border-emerald-500/30 transition">
      <div className="flex justify-between items-start">
        <div>
          <h4 className="text-base font-bold text-white font-mono">
            {county.name} County, {state}
          </h4>
          <span className="text-xs font-mono text-slate-400">
            Jurisdiction Tier: {tier} · Portal: {county.court_portal}
          </span>
        </div>
        <span
          className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold ${getStatusBadgeClass(status)}`}
        >
          {status}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2 py-2 bg-slate-950/60 rounded-lg p-3 border border-slate-800/80 text-center font-mono">
        <div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wider">Active Dockets</div>
          <div className="text-sm font-bold text-white mt-0.5">{county.cases_count}</div>
        </div>
        <div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wider">Qualified Leads</div>
          <div className="text-sm font-bold text-emerald-400 mt-0.5">{county.opportunities_count}</div>
        </div>
        <div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wider">Expansion Score</div>
          <div className="text-sm font-bold text-blue-400 mt-0.5">{county.expansion_score} / 100</div>
        </div>
      </div>
      <div className="space-y-1.5 text-xs font-mono text-slate-300 pt-2 border-t border-slate-800">
        <div className="flex justify-between">
          <span className="text-slate-500">Median Home Value:</span>
          <span className="font-semibold text-slate-200">
            {formatPrice(county.median_home_price)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Pipeline Conversion:</span>
          <span className="text-emerald-400 font-bold">
            {formatConversion(county.conversion_rate)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Strategic Disposition:</span>
          <span className="text-amber-400 font-medium">{county.recommendation}</span>
        </div>
      </div>
    </div>
  );
};

export const CountyRadarView: React.FC<CountyRadarViewProps> = ({ countyBoard, loading }) => {
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-16 text-slate-500 font-mono text-sm">
          Loading jurisdictional court feeds & county intelligence...
        </div>
      </div>
    );
  }

  if (countyBoard.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-16 text-slate-500 font-mono text-sm">
          No active counties indexed in platform database.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        {countyBoard.map((c) => (
          <CountyCard key={c.county_id || c.name} county={c} />
        ))}
      </div>
    </div>
  );
};

