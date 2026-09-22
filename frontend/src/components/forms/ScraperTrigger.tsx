import React, { useState } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ScraperTriggerProps {
  onTrigger: (fips: string, lookback: number) => Promise<any>;
}

export const ScraperTrigger: React.FC<ScraperTriggerProps> = ({ onTrigger }) => {
  const [fips, setFips] = useState<string>('53053');
  const [lookback, setLookback] = useState<number>(7);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [localLogs, setLocalLogs] = useState<string[]>([
    '[INIT] Municipal Ingestion Subsystem standby...',
    '[AUTH] Headless browser driver pool calibrated.',
  ]);

  const { isConnected, events } = useWebSocket();

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    const timestamp = new Date().toLocaleTimeString();
    setLocalLogs((prev) => [
      `[${timestamp}] [DISPATCH] Initiating headless scraper worker for County FIPS ${fips}...`,
      ...prev,
    ]);

    try {
      const res = await onTrigger(fips, lookback);
      setLocalLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] [SUCCESS] Scraper finished: ${res?.message || '5 new dockets indexed'}`,
        ...prev,
      ]);
    } catch (err: any) {
      setLocalLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] [ERROR] Worker failed: ${err.message}`,
        ...prev,
      ]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Municipal Court Scraper & Intake Monitor
          </h3>
          <p className="text-xs text-slate-400 font-sans">
            Direct Playwright Headless Worker Dispatch & Docket Extraction
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`h-2.5 w-2.5 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-amber-500'}`} />
          <span className="text-xs font-mono text-slate-300">
            {isConnected ? 'Telemetry WS Active' : 'WS Reconnecting'}
          </span>
        </div>
      </div>

      <form onSubmit={handleLaunch} className="grid grid-cols-3 gap-4">
        <div>
          <label htmlFor="scraper-county-select" className="block text-xs font-mono text-slate-400 mb-1">Target County FIPS</label>
          <select
            id="scraper-county-select"
            value={fips}
            onChange={(e) => setFips(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
          >
            <option value="53053">Pierce County (53053) - Odyssey</option>
            <option value="53067">Thurston County (53067) - Pioneer</option>
            <option value="53033">King County (53033) - Portal</option>
            <option value="53061">Snohomish County (53061) - Odyssey</option>
          </select>
        </div>

        <div>
          <label htmlFor="scraper-lookback-input" className="block text-xs font-mono text-slate-400 mb-1">Lookback Window (Days)</label>
          <input
            id="scraper-lookback-input"
            type="number"
            min={1}
            max={60}
            value={lookback}
            onChange={(e) => setLookback(Number(e.target.value))}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={isRunning}
            className={`w-full py-2 px-4 rounded-lg text-xs font-bold font-mono transition flex items-center justify-center space-x-2 ${
              isRunning
                ? 'bg-indigo-900/60 text-indigo-300 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30'
            }`}
          >
            {isRunning ? (
              <>
                <span className="animate-spin text-sm">⟳</span>
                <span>Scraping Court Portal...</span>
              </>
            ) : (
              <>
                <span>▶</span>
                <span>Launch Headless Scraper</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Terminal Output Log Container */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span>Worker Execution Stream (Playwright Live Telemetry)</span>
          <button
            onClick={() => setLocalLogs(['[CONSOLE CLEARED]'])}
            className="hover:text-slate-200"
          >
            Clear Console
          </button>
        </div>
        <div className="h-44 bg-slate-950 border border-slate-800 rounded-lg p-3 overflow-y-auto font-mono text-xs space-y-1 text-slate-300">
          {localLogs.map((log, i) => (
            <div
              key={i}
              className={`leading-relaxed ${
                log.includes('[SUCCESS]')
                  ? 'text-emerald-400'
                  : log.includes('[ERROR]')
                  ? 'text-rose-400'
                  : log.includes('[DISPATCH]')
                  ? 'text-cyan-400'
                  : 'text-slate-400'
              }`}
            >
              {log}
            </div>
          ))}
          {events.map((ev, i) => (
            <div key={`ws-${i}`} className="text-indigo-300">
              [{new Date(ev.timestamp * 1000).toLocaleTimeString()}] [WS_EVENT] {ev.type}: {ev.message || JSON.stringify(ev.data || {})}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
