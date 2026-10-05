import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Filter, TrendingUp } from 'lucide-react';

interface StatsResponse {
  total_saved?: number;
  total_tailored?: number;
  total_applied?: number;
  total_interview?: number;
  total_offer?: number;
  total_rejected?: number;
  avg_score?: number;
  response_rate?: number;
}

/**
 * Application Funnel — Discovered -> Saved -> Applied -> Interview -> Offer.
 * Data: GET /api/stats (rule-based SQL, zero LLM cost) + live jobs count.
 * Bars animate on data change only; no idle timers.
 */
export default function FunnelPanel({ discovered }: { discovered: number }) {
  const { data: stats } = useQuery<StatsResponse>({
    queryKey: ['funnelStats'],
    queryFn: async () => {
      const res = await fetch('/api/stats');
      if (!res.ok) throw new Error(`stats ${res.status}`);
      return res.json();
    },
    refetchInterval: 30000,
  });

  const stages = [
    { label: 'Discovered', value: discovered, color: 'from-sky-500/70 to-sky-400/70' },
    { label: 'Saved', value: stats?.total_saved ?? 0, color: 'from-indigo-500/70 to-indigo-400/70' },
    { label: 'Applied', value: stats?.total_applied ?? 0, color: 'from-violet-500/70 to-violet-400/70' },
    { label: 'Interview', value: stats?.total_interview ?? 0, color: 'from-fuchsia-500/70 to-fuchsia-400/70' },
    { label: 'Offer', value: stats?.total_offer ?? 0, color: 'from-emerald-500/70 to-emerald-400/70' },
  ];
  const max = Math.max(1, ...stages.map((s) => s.value));

  return (
    <div className="p-4 rounded-2xl bg-white/[0.015] border border-white/[0.05] space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
          <Filter size={13} className="text-indigo-400" />
          Application Funnel
        </h3>
        {(stats?.response_rate ?? 0) > 0 && (
          <span
            className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-mono flex items-center gap-1"
            title="Interviews + Offers + Rejections over total applications"
          >
            <TrendingUp size={10} />
            {stats?.response_rate}% response
          </span>
        )}
      </div>

      <div className="space-y-2">
        {stages.map((s) => (
          <div key={s.label} className="flex items-center gap-2.5">
            <span className="w-16 shrink-0 text-[10px] uppercase tracking-wider text-zinc-500">{s.label}</span>
            <div className="flex-1 h-4 rounded-md bg-white/[0.03] overflow-hidden">
              <div
                className={`h-full rounded-md bg-gradient-to-r ${s.color} transition-all duration-700 ease-out`}
                style={{ width: `${(s.value / max) * 100}%` }}
              />
            </div>
            <span className="w-7 text-right text-[11px] font-mono font-bold text-zinc-300">{s.value}</span>
          </div>
        ))}
      </div>

      {(stats?.avg_score ?? 0) > 0 && (
        <div className="pt-1 text-[10px] text-zinc-500 font-mono">
          avg match across pipeline: {stats?.avg_score}%
        </div>
      )}
    </div>
  );
}
