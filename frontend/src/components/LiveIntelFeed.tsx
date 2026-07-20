import React from 'react';
import { Building, MapPin, DollarSign, Clock, CheckCircle2, AlertCircle, ShieldCheck, ArrowUpRight, Loader2 } from 'lucide-react';
import type { JobViewV2 } from '../api/v2Client';

interface LiveIntelFeedProps {
  jobs: JobViewV2[];
  isLoading: boolean;
  onSelectJob: (job: JobViewV2) => void;
  selectedJobId?: number;
}

export default function LiveIntelFeed({ jobs, isLoading, onSelectJob, selectedJobId }: LiveIntelFeedProps) {
  if (isLoading) {
    return (
      <div className="w-full py-16 flex flex-col items-center justify-center text-zinc-500 gap-3">
        <Loader2 size={28} className="animate-spin text-indigo-400" />
        <p className="text-sm font-medium">Loading Live Intel feed from database...</p>
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
          Use the Central Command Bar above to run a search across live sources (RemoteOK, Arbeitnow, HackerNews, LinkedIn).
        </p>
      </div>
    );
  }

  const getScoreColor = (score?: number | null) => {
    if (score == null) return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20';
    if (score >= 80) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30 shadow-[0_0_12px_-3px_rgba(52,211,153,0.3)]';
    if (score >= 60) return 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30';
    if (score >= 40) return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    return 'bg-red-500/15 text-red-400 border-red-500/30';
  };

  return (
    <div className="space-y-3">
      {jobs.map((job) => {
        const isSelected = selectedJobId === job.id;
        const scoreBadgeColor = getScoreColor(job.match_score);
        
        return (
          <div
            key={job.id}
            onClick={() => onSelectJob(job)}
            className={`p-4 rounded-xl border transition-all cursor-pointer group relative ${
              isSelected
                ? 'bg-indigo-500/[0.08] border-indigo-500/60 shadow-[0_0_20px_-5px_rgba(99,102,241,0.25)]'
                : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04] hover:border-indigo-500/30'
            }`}
          >
            <div className="flex justify-between items-start gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-bold text-base text-white group-hover:text-indigo-300 transition-colors truncate">
                    {job.title}
                  </h3>
                  {job.remote && (
                    <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[10px] font-mono uppercase">
                      Remote
                    </span>
                  )}
                  {job.status && job.status !== 'Saved' && (
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono flex items-center gap-1">
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
                    <span className="flex items-center gap-1 text-emerald-400 font-medium">
                      <DollarSign size={13} />
                      {job.salary_min ? `${(job.salary_min / 1000).toFixed(0)}k` : ''}
                      {job.salary_min && job.salary_max ? ' - ' : ''}
                      {job.salary_max ? `${(job.salary_max / 1000).toFixed(0)}k` : ''}
                      {job.currency ? ` ${job.currency}` : ''}
                    </span>
                  )}
                  {job.posted_at && (
                    <span className="flex items-center gap-1 text-zinc-500">
                      <Clock size={13} />
                      {job.posted_at}
                    </span>
                  )}
                </div>
              </div>

              {/* Score & Action Indicator */}
              <div className="flex flex-col items-end gap-2 shrink-0">
                <div className={`px-2.5 py-1 rounded-lg border text-xs font-mono font-bold flex items-center gap-1.5 ${scoreBadgeColor}`}>
                  <span>{job.match_score != null ? `${job.match_score}% Match` : 'Unscored'}</span>
                </div>
                
                {job.match_reason && (
                  <span className="text-[10px] text-zinc-500 flex items-center gap-1 group-hover:text-zinc-400">
                    <ShieldCheck size={11} className="text-indigo-400" />
                    Audited
                  </span>
                )}
              </div>
            </div>

            {job.description && (
              <p className="mt-3 text-xs text-zinc-400 line-clamp-2 leading-relaxed opacity-90 group-hover:opacity-100 transition-opacity">
                {job.description}
              </p>
            )}

            <div className="mt-3 pt-2.5 border-t border-white/[0.04] flex items-center justify-between text-[11px] text-zinc-500">
              <span className="truncate max-w-[75%]">
                {job.match_reason ? `Why fits: ${job.match_reason}` : 'Click to inspect description, score breakdown & audit capability.'}
              </span>
              <span className="text-indigo-400 opacity-0 group-hover:opacity-100 flex items-center gap-0.5 font-medium transition-opacity">
                Inspect <ArrowUpRight size={13} />
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
