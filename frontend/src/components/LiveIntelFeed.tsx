import React from 'react';
import {
  Building,
  MapPin,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ArrowUpRight,
  Loader2,
  Sparkles,
} from 'lucide-react';
import type { JobViewV2 } from '../api/v2Client';

interface LiveIntelFeedProps {
  jobs: JobViewV2[];
  isLoading: boolean;
  onSelectJob: (job: JobViewV2) => void;
  selectedJobId?: number;
  onOpenAtsBreakdown?: (job: JobViewV2) => void;
}

/** Human relative time for ISO-ish timestamps; falls back to raw text. */
function relativeTime(raw?: string | null): string {
  if (!raw) return '';
  const ts = Date.parse(raw);
  if (Number.isNaN(ts)) return raw.length > 32 ? raw.slice(0, 32) + '…' : raw;
  const diff = Date.now() - ts;
  if (diff < 0) return 'just now';
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}

export default function LiveIntelFeed({ jobs, isLoading, onSelectJob, selectedJobId, onOpenAtsBreakdown }: LiveIntelFeedProps) {
  if (isLoading) {
    return (
      <div className="w-full py-16 flex flex-col items-center justify-center text-zinc-500 gap-3">
        <Loader2 size={28} className="animate-spin text-indigo-400" />
        <p className="text-sm font-medium">Querying vector pipeline & job database...</p>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="w-full py-16 px-6 rounded-2xl bg-white/[0.015] border border-white/[0.05] flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-3">
          <AlertCircle size={24} />
        </div>
        <h3 className="text-base font-bold text-white">No Jobs Found in Pipeline</h3>
        <p className="text-xs text-zinc-400 max-w-sm mt-1">
          Use the Search Bar above to run an active scrape across RemoteOK, Jobicy, Arbeitnow, and LinkedIn.
        </p>
      </div>
    );
  }

  const getScoreBadge = (score?: number | null) => {
    if (score == null) return { color: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20', glow: '' };
    if (score >= 80) return { color: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30', glow: 'shadow-[0_0_16px_-3px_rgba(52,211,153,0.4)]' };
    if (score >= 65) return { color: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30', glow: 'shadow-[0_0_16px_-3px_rgba(99,102,241,0.35)]' };
    if (score >= 45) return { color: 'bg-amber-500/15 text-amber-300 border-amber-500/30', glow: 'shadow-[0_0_16px_-3px_rgba(251,191,36,0.3)]' };
    return { color: 'bg-rose-500/15 text-rose-300 border-rose-500/30', glow: '' };
  };

  return (
    <div className="space-y-3">
      {jobs.map((job) => {
        const isSelected = selectedJobId === job.id;
        const scoreBadge = getScoreBadge(job.match_score);
        const companyInitial = (job.company || 'C').charAt(0).toUpperCase();

        return (
          <div
            key={job.id}
            role="button"
            tabIndex={0}
            aria-label={`Open job: ${job.title}`}
            aria-pressed={isSelected}
            onClick={() => onSelectJob(job)}
            onKeyDown={(e) => {
              if (e.target !== e.currentTarget) return;
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelectJob(job);
              }
            }}
            className={`p-4 md:p-4.5 rounded-2xl border transition-all duration-300 ease-out cursor-pointer group relative focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/70 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] ${
              isSelected
                ? 'bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-black/40 border-indigo-500/60 shadow-[0_16px_36px_rgba(0,0,0,0.6),0_0_30px_-5px_rgba(99,102,241,0.3)] -translate-y-0.5'
                : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04] hover:border-indigo-500/40 hover:-translate-y-1 hover:shadow-[0_20px_40px_rgba(0,0,0,0.5),0_0_24px_-4px_rgba(99,102,241,0.2)]'
            }`}
          >
            <div className="flex justify-between items-start gap-4">
              <div className="flex items-start gap-3.5 flex-1 min-w-0">
                {/* Company Initial Emblem */}
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-white/[0.08] to-white/[0.02] border border-white/[0.1] flex items-center justify-center font-bold text-sm text-white group-hover:border-indigo-500/40 group-hover:text-indigo-300 transition-colors shrink-0 shadow-inner">
                  {companyInitial}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-bold text-base text-white group-hover:text-indigo-300 transition-colors truncate">
                      {job.title}
                    </h3>
                    {job.remote && (
                      <span className="px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/25 text-[10px] font-mono font-medium uppercase">
                        Remote
                      </span>
                    )}
                    {job.status && job.status !== 'Saved' && (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 text-[10px] font-mono flex items-center gap-1 font-medium">
                        <CheckCircle2 size={10} />
                        {job.status}
                      </span>
                    )}
                  </div>

                  <div className="mt-1.5 flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-zinc-400">
                    <span className="flex items-center gap-1 font-medium text-zinc-300">
                      <Building size={13} className="text-zinc-500" />
                      {job.company}
                    </span>
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <MapPin size={13} className="text-zinc-500" />
                        {job.location}
                      </span>
                    )}
                    {(job.salary_min || job.salary_max) && (
                      <span className="flex items-center gap-1 text-emerald-400 font-semibold font-mono">
                        <DollarSign size={13} />
                        {job.salary_min ? `${(job.salary_min / 1000).toFixed(0)}k` : ''}
                        {job.salary_min && job.salary_max ? ' - ' : ''}
                        {job.salary_max ? `${(job.salary_max / 1000).toFixed(0)}k` : ''}
                        {job.currency ? ` ${job.currency}` : ''}
                      </span>
                    )}
                    {job.posted_at && (
                      <span className="flex items-center gap-1 text-zinc-500" title={job.posted_at}>
                        <Clock size={13} />
                        {relativeTime(job.posted_at)}
                      </span>
                    )}

                    {/* Freshness warning badge */}
                    {job.posted_at && (() => {
                      const ts = Date.parse(job.posted_at);
                      if (Number.isNaN(ts)) return null;
                      const daysOld = Math.floor((Date.now() - ts) / 86400000);
                      if (daysOld > 30)
                        return (
                          <span className="px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/25 text-[9px] font-bold uppercase">
                            Expired?
                          </span>
                        );
                      if (daysOld > 14)
                        return (
                          <span className="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/25 text-[9px] font-bold uppercase">
                            Stale
                          </span>
                        );
                      return (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] font-bold uppercase">
                          Recent
                        </span>
                      );
                    })()}
                  </div>
                </div>
              </div>

              {/* Match Score Gauge Pill */}
              <div className="flex flex-col items-end gap-1.5 shrink-0">
                <div
                  className={`px-3 py-1.5 rounded-xl border text-xs font-mono font-bold flex items-center gap-1.5 ${scoreBadge.color} ${scoreBadge.glow}`}
                >
                  <Sparkles size={12} />
                  <span>{job.match_score != null ? `${job.match_score}% Match` : 'Pending'}</span>
                </div>

                {job.match_reason && (
                  <span className="text-[10px] text-zinc-500 flex items-center gap-1 group-hover:text-zinc-400">
                    <ShieldCheck size={11} className="text-indigo-400" />
                    Rubric Audited
                  </span>
                )}
              </div>
            </div>

            {/* Description Snippet */}
            {job.description && (
              <p className="mt-3 text-xs text-zinc-400 line-clamp-2 leading-relaxed opacity-85 group-hover:opacity-100 transition-opacity">
                {job.description}
              </p>
            )}

            {/* Bottom Insight & Quick Action */}
            <div className="mt-3 pt-2.5 border-t border-white/[0.04] flex items-center justify-between text-[11px] text-zinc-500">
              <span className="truncate max-w-[60%]">
                {job.match_reason ? (
                  <span className="text-zinc-400">
                    <b className="text-indigo-300 font-medium">Why it fits:</b> {job.match_reason}
                  </span>
                ) : (
                  'Click to inspect recruiter score rubric & trigger 1-click tailored resume.'
                )}
              </span>
              <div className="flex items-center gap-2">
                {onOpenAtsBreakdown && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenAtsBreakdown(job);
                    }}
                    className="px-2 py-0.5 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/25 border border-indigo-500/30 text-indigo-300 font-mono text-[10px] font-bold flex items-center gap-1 transition-colors"
                  >
                    <ShieldCheck size={11} /> ATS Gap Matrix
                  </button>
                )}
                <span className="text-indigo-400 opacity-80 group-hover:opacity-100 flex items-center gap-1 font-semibold group-hover:translate-x-0.5 transition-all">
                  Inspect <ArrowUpRight size={13} />
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
