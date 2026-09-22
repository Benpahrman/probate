import React, { useState } from 'react';
import { OwnershipProfile } from '../../types';

interface EquityWaterfallProps {
  ownership: OwnershipProfile;
  avmValue: number;
}

export const EquityWaterfall: React.FC<EquityWaterfallProps> = ({ ownership, avmValue }) => {
  const [customOffer, setCustomOffer] = useState<number>(ownership.target_wholesale_mao || Math.round(avmValue * 0.7));

  const totalEncumbrances =
    (ownership.senior_mortgage_balance || 0) +
    (ownership.municipal_liens || 0) +
    (ownership.estimated_repairs || 0);

  const netEquity = Math.max(0, avmValue - totalEncumbrances);
  const netEquityPct = avmValue > 0 ? (netEquity / avmValue) * 100 : 0;

  // Simulator calculations
  const sellerProceeds = Math.max(0, customOffer - (ownership.senior_mortgage_balance || 0) - (ownership.municipal_liens || 0));
  const wholesaleSpread = Math.max(0, Math.round(avmValue * 0.85) - customOffer);

  const formatUSD = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            2. Verified Ownership & Equity Waterfall
          </h4>
          <p className="text-xs text-slate-400 font-sans">Institutional Title & Lien Encumbrance Stack</p>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/80 px-2.5 py-1 rounded border border-emerald-800/80">
            {netEquityPct.toFixed(1)}% Distributable Equity
          </span>
        </div>
      </div>

      {/* Dynamic Stack Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-slate-400 font-mono">
          <span>Net Equity: {formatUSD(netEquity)}</span>
          <span>AVM Valuation: {formatUSD(avmValue)}</span>
        </div>
        <div className="w-full h-4 bg-slate-950 rounded-full overflow-hidden flex border border-slate-800">
          <div
            style={{ width: `${Math.min(100, Math.max(0, netEquityPct))}%` }}
            className="bg-emerald-500 transition-all duration-500 relative group"
            title={`Net Equity: ${formatUSD(netEquity)}`}
          />
          <div
            style={{ width: `${Math.min(100, 100 - netEquityPct)}%` }}
            className="bg-rose-600 transition-all duration-500 relative group"
            title={`Total Liens: ${formatUSD(totalEncumbrances)}`}
          />
        </div>
      </div>

      {/* Waterfall Line Items */}
      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 space-y-2">
          <div className="flex justify-between text-slate-300">
            <span>AVM Baseline:</span>
            <span className="font-bold text-white">{formatUSD(avmValue)}</span>
          </div>
          <div className="flex justify-between text-rose-400">
            <span>Senior Mortgage:</span>
            <span>-{formatUSD(ownership.senior_mortgage_balance || 0)}</span>
          </div>
          <div className="flex justify-between text-rose-400">
            <span>Municipal/Tax Liens:</span>
            <span>-{formatUSD(ownership.municipal_liens || 0)}</span>
          </div>
          <div className="flex justify-between text-rose-400">
            <span>Est. Renovation/Repairs:</span>
            <span>-{formatUSD(ownership.estimated_repairs || 0)}</span>
          </div>
          <div className="border-t border-slate-800 pt-1.5 flex justify-between font-bold text-emerald-400 text-sm">
            <span>NET DISTRIBUTABLE:</span>
            <span>{formatUSD(netEquity)}</span>
          </div>
        </div>

        {/* Interactive Acquisition Simulator */}
        <div className="p-3 bg-indigo-950/30 rounded-lg border border-indigo-900/50 space-y-2">
          <div className="flex items-center justify-between text-indigo-300 font-bold">
            <span>ACQUISITION SIMULATOR</span>
            <span className="text-[10px] bg-indigo-900/60 px-1.5 py-0.5 rounded text-indigo-200">Interactive</span>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-slate-300">
              <label htmlFor="custom-offer-input">Target Offer Figure:</label>
              <span className="font-bold text-white">{formatUSD(customOffer)}</span>
            </div>
            <input
              id="custom-offer-input"
              type="range"
              min={Math.max(10000, totalEncumbrances)}
              max={avmValue}
              step={5000}
              value={customOffer}
              onChange={(e) => setCustomOffer(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
          </div>
          <div className="pt-2 border-t border-indigo-900/40 space-y-1">
            <div className="flex justify-between text-emerald-400">
              <span>Projected Seller Net:</span>
              <span className="font-bold">{formatUSD(sellerProceeds)}</span>
            </div>
            <div className="flex justify-between text-cyan-400">
              <span>Wholesale Spread Potential:</span>
              <span className="font-bold">{formatUSD(wholesaleSpread)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
