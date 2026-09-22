import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: string;
  trendPositive?: boolean;
  icon?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  trend,
  trendPositive,
  icon,
  className = '',
}) => {
  return (
    <div className={`p-5 bg-slate-900/90 border border-slate-800 rounded-xl shadow-md hover:border-slate-700 transition ${className}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
          {label}
        </span>
        {icon && <span className="text-lg opacity-80">{icon}</span>}
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-black tracking-tight text-white font-mono">
          {value}
        </span>
        {trend && (
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              trendPositive
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                : 'bg-rose-950 text-rose-400 border border-rose-800/60'
            }`}
          >
            {trend}
          </span>
        )}
      </div>
      {subtext && (
        <p className="mt-1.5 text-xs text-slate-500 font-sans">{subtext}</p>
      )}
    </div>
  );
};
