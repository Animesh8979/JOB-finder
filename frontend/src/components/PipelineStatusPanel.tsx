import React from 'react';
import { Terminal, Activity, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';
import type { RunViewV2 } from '../api/v2Client';

interface PipelineStatusPanelProps {
  runs: RunViewV2[];
  activeRunId?: string | null;
  onRefreshRuns: () => void;
}

export default function PipelineStatusPanel({ runs, activeRunId, onRefreshRuns }: PipelineStatusPanelProps) {
  const activeRuns = runs.filter(r => r.status === 'queued' || r.status === 'running');
  const finishedRuns = runs.filter(r => r.status === 'completed' || r.status === 'failed').slice(0, 5);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'queued':
        return <Activity size={14} className="text-indigo-400 animate-pulse" />;
      case 'completed':
        return <CheckCircle2 size={14} className="text-emerald-400" />;
      case 'failed':
        return <AlertTriangle size={14} className="text-red-400" />;
      default:
        return <Terminal size={14} className="text-zinc-500" />;
    }
  };

  return (
    <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.05] flex flex-col gap-5 h-full min-h-[400px]">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
        <h2 className="text-xs font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
          <Activity size={15} className="text-indigo-400" />
          Pipeline Operations ({activeRuns.length} Active)
        </h2>
        <button
          onClick={onRefreshRuns}
          className="p-1 rounded hover:bg-white/5 text-zinc-500 hover:text-white transition-colors"
          title="Refresh Queue"
        >
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Active Runs Section */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-zinc-300">Active / Queued Jobs</h3>
        {activeRuns.length === 0 ? (
          <div className="p-4 rounded-xl bg-white/[0.01] border border-white/[0.04] text-center text-zinc-500 text-xs">
            No jobs currently running in the background.
          </div>
        ) : (
          activeRuns.map((run) => {
            const progress = run.progress_total && run.progress_total > 0
              ? Math.round(((run.progress_current || 0) / run.progress_total) * 100)
              : run.status === 'running' ? 50 : 10;
            const isSelected = activeRunId === run.run_id;

            return (
              <div
                key={run.run_id}
                className={`p-3.5 rounded-xl border transition-all ${
                  isSelected
                    ? 'bg-indigo-500/10 border-indigo-500/50'
                    : 'bg-white/[0.02] border-white/[0.06]'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(run.status)}
                    <span className="text-xs font-bold text-white uppercase tracking-wide">
                      {run.kind}
                    </span>
                    {run.phase && (
                      <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-mono">
                        {run.phase}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono font-bold text-indigo-400">
                    {progress}%
                  </span>
                </div>

                {run.message && (
                  <p className="text-xs text-zinc-400 mb-2 truncate">
                    {run.message}
                  </p>
                )}

                {/* Progress Bar */}
                <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Recent History Section */}
      <div className="space-y-3 flex-1">
        <h3 className="text-xs font-semibold text-zinc-300">Execution History</h3>
        {finishedRuns.length === 0 ? (
          <div className="p-6 rounded-xl bg-white/[0.01] border border-white/[0.04] flex flex-col items-center justify-center text-center text-zinc-500 gap-2">
            <Terminal size={24} className="opacity-40" />
            <p className="text-xs">No recent task logs.</p>
          </div>
        ) : (
          <div className="space-y-2 overflow-y-auto max-h-[260px] pr-1 custom-scrollbar">
            {finishedRuns.map((run) => (
              <div
                key={run.run_id}
                className="p-3 rounded-lg bg-white/[0.015] border border-white/[0.04] text-xs flex items-center justify-between gap-3"
              >
                <div className="flex items-center gap-2 min-w-0">
                  {getStatusIcon(run.status)}
                  <span className="font-medium text-zinc-300 truncate">{run.kind}</span>
                  {run.message && (
                    <span className="text-zinc-500 truncate max-w-[120px]">({run.message})</span>
                  )}
                </div>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                  run.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                }`}>
                  {run.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
