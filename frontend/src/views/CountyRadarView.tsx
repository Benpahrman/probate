import React from 'react';

interface CountyRadarViewProps {
  countyBoard: any[];
  loading: boolean;
}

export const CountyRadarView: React.FC<CountyRadarViewProps> = ({ countyBoard, loading }) => {
  return (
    <div className="space-y-6">
      {loading ? (
        <div className="text-center py-16 text-slate-500 font-mono text-sm">
          Loading jurisdictional court feeds & county intelligence...
        </div>
      ) : countyBoard.length === 0 ? (
        <div className="text-center py-16 text-slate-500 font-mono text-sm">
          No active counties indexed in platform database.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          {countyBoard.map((c) => (
            <div
              key={c.county_id || c.name}
              className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 hover:border-emerald-500/30 transition"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-base font-bold text-white font-mono">
                    {c.name} County, {c.state || 'WA'}
                  </h4>
                  <span className="text-xs font-mono text-slate-400">
                    Jurisdiction Tier: {c.tier || 1} · Portal: {c.court_portal}
                  </span>
                </div>
                <span
                  className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold ${
                    c.status === 'ACTIVE'
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-amber-950 text-amber-400 border border-amber-800'
                  }`}
                >
                  {c.status || 'ACTIVE'}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 py-2 bg-slate-950/60 rounded-lg p-3 border border-slate-800/80 text-center font-mono">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Active Dockets</div>
                  <div className="text-sm font-bold text-white mt-0.5">{c.cases_count}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Qualified Leads</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5">{c.opportunities_count}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Expansion Score</div>
                  <div className="text-sm font-bold text-blue-400 mt-0.5">{c.expansion_score} / 100</div>
                </div>
              </div>
              <div className="space-y-1.5 text-xs font-mono text-slate-300 pt-2 border-t border-slate-800">
                <div className="flex justify-between">
                  <span className="text-slate-500">Median Home Value:</span>
                  <span className="font-semibold text-slate-200">
                    {c.median_home_price ? `$${c.median_home_price.toLocaleString()}` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Pipeline Conversion:</span>
                  <span className="text-emerald-400 font-bold">
                    {c.conversion_rate !== null && c.conversion_rate !== undefined ? `${c.conversion_rate}%` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Strategic Disposition:</span>
                  <span className="text-amber-400 font-medium">{c.recommendation}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
