/**
 * LiveTicker — continuously scrolling "data ribbon" used at the top of the
 * Dashboard hero. Visually cinematic, low-cost: uses CSS marquee + duplicated
 * content. The contents are recent telemetry (job counts, found/scored, etc.).
 */
import React, { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';

interface TickerStat {
  label: string;
  value: string | number;
  tone?: 'ok' | 'warn' | 'accent';
}

interface LiveTickerProps {
  refreshMs?: number;
  fetcher?: () => Promise<TickerStat[]>;
  fallback?: TickerStat[];
}

const TONE: Record<string, string> = {
  ok: 'text-emerald-300',
  warn: 'text-amber-300',
  accent: 'text-violet-300',
};

export default function LiveTicker({
  refreshMs = 12000,
  fetcher,
  fallback = [
    { label: 'scout', value: 'idle' },
    { label: 'curated', value: '0' },
    { label: 'tailored', value: '0' },
  ],
}: LiveTickerProps) {
  const [stats, setStats] = useState<TickerStat[]>(fallback);

  useEffect(() => {
    if (!fetcher) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const result = await fetcher();
        if (!cancelled && result.length) setStats(result);
      } catch {
        /* ignore */
      }
    };
    tick();
    const t = setInterval(tick, refreshMs);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [fetcher, refreshMs]);

  // Duplicate to make the loop seamless.
  const looped = [...stats, ...stats];

  return (
    <div className="relative overflow-hidden rounded-xl border border-white/5 bg-white/[0.02] py-2.5">
      <div className="marquee-track gap-10 px-4 text-[11px] font-medium tracking-[0.18em] uppercase">
        {looped.map((s, i) => (
          <span key={i} className="flex items-center gap-2 whitespace-nowrap">
            <Sparkles size={11} className={TONE[s.tone || 'accent'] || ''} />
            <span className={TONE[s.tone || 'accent'] || 'text-zinc-300'}>{s.label}</span>
            <span className="text-zinc-100 tabnum">{s.value}</span>
          </span>
        ))}
      </div>
      {/* edge fades */}
      <div className="pointer-events-none absolute inset-y-0 left-0 w-20 bg-gradient-to-r from-[#030303] to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-20 bg-gradient-to-l from-[#030303] to-transparent" />
    </div>
  );
}
