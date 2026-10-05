/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from 'react';
import { X, Building, MapPin, DollarSign, ShieldCheck, Sparkles, FileText, Send, ExternalLink, Loader2 } from 'lucide-react';
import { triggerAuditV2, triggerApplyV2, type JobViewV2, type RunViewV2 } from '../api/v2Client';
import toast from 'react-hot-toast';

interface JobDetailDrawerProps {
  job: JobViewV2 | null;
  onClose: () => void;
  onOpenTailor: (job: JobViewV2) => void;
  onOpenPrepareApply: (job: JobViewV2, run?: RunViewV2) => void;
  onAuditStarted: (runId: string) => void;
}

export default function JobDetailDrawer({
  job,
  onClose,
  onOpenTailor,
  onOpenPrepareApply,
  onAuditStarted
}: JobDetailDrawerProps) {
  const [isAuditing, setIsAuditing] = useState(false);
  const [isPreparing, setIsPreparing] = useState(false);
  const [agReport, setAgReport] = useState<any>(null);
  const [isLoadingAg, setIsLoadingAg] = useState(false);

  if (!job) return null;

  const handleFetchAgEval = async () => {
    setIsLoadingAg(true);
    try {
      const res = await fetch(`/api/jobs/${job.id}/ag-eval`);
      if (res.ok) {
        const data = await res.json();
        setAgReport(data);
        toast.success("7-Block CareerOps Evaluation Loaded!");
      } else {
        toast.error("Failed to load A-G evaluation.");
      }
    } catch {
      toast.error("Network error fetching A-G evaluation.");
    } finally {
      setIsLoadingAg(false);
    }
  };

  const handleRunAudit = async () => {
    setIsAuditing(true);
    try {
      const run = await triggerAuditV2(job.id);
      toast.success(`Capability audit initiated (${run.run_id})`);
      onAuditStarted(run.run_id);
    } catch (e: unknown) {
      toast.error(`Audit trigger failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsAuditing(false);
    }
  };

  const handlePrepareApply = async () => {
    setIsPreparing(true);
    try {
      const run = await triggerApplyV2(job.id);
      toast.success('Staged application prepared for review!');
      onOpenPrepareApply(job, run);
    } catch (e: unknown) {
      toast.error(`Failed to stage application: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsPreparing(false);
    }
  };

  const getScoreColor = (score?: number | null) => {
    if (score == null) return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20';
    if (score >= 80) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
    if (score >= 60) return 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30';
    return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end animate-in fade-in duration-200">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Content */}
      <div className="relative w-full max-w-2xl bg-[#0e0e12] border-l border-white/10 h-full flex flex-col shadow-2xl z-10 overflow-hidden">
        
        {/* Drawer Header */}
        <div className="p-6 border-b border-white/10 flex items-start justify-between gap-4 bg-white/[0.01]">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <h2 className="text-xl font-bold text-white">{job.title}</h2>
              {job.remote && (
                <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-xs font-mono">
                  Remote
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-zinc-400">
              <span className="flex items-center gap-1.5 text-zinc-200 font-medium">
                <Building size={15} className="text-indigo-400" />
                {job.company}
              </span>
              {job.location && (
                <span className="flex items-center gap-1.5">
                  <MapPin size={15} className="text-zinc-500" />
                  {job.location}
                </span>
              )}
              {(job.salary_min || job.salary_max) && (
                <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <DollarSign size={15} />
                  {job.salary_min ? `${(job.salary_min / 1000).toFixed(0)}k` : ''}
                  {job.salary_min && job.salary_max ? ' - ' : ''}
                  {job.salary_max ? `${(job.salary_max / 1000).toFixed(0)}k` : ''}
                </span>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white transition-colors shrink-0"
          >
            <X size={18} />
          </button>
        </div>

        {/* Action Bar */}
        <div className="p-4 bg-indigo-500/[0.04] border-b border-white/10 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className={`px-3 py-1.5 rounded-xl border text-xs font-mono font-bold flex items-center gap-1.5 ${getScoreColor(job.match_score)}`}>
              <Sparkles size={14} />
              <span>{job.match_score != null ? `${job.match_score}% Fit Score` : 'Not Audited'}</span>
            </div>
            {job.url && (
              <a
                href={job.url}
                target="_blank"
                rel="noreferrer"
                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white text-xs flex items-center gap-1 transition-colors"
              >
                <span>Original Post</span>
                <ExternalLink size={12} />
              </a>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleFetchAgEval}
              disabled={isLoadingAg}
              className="px-3.5 py-2 rounded-xl bg-indigo-500/20 border border-indigo-500/40 hover:bg-indigo-500/30 text-indigo-200 text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              {isLoadingAg ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
              <span>A–G Rubric</span>
            </button>

            <button
              onClick={handleRunAudit}
              disabled={isAuditing}
              className="px-3.5 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              {isAuditing ? <Loader2 size={14} className="animate-spin" /> : <ShieldCheck size={14} className="text-indigo-400" />}
              <span>Capability Audit</span>
            </button>

            <button
              onClick={() => onOpenTailor(job)}
              className="px-3.5 py-2 rounded-xl bg-indigo-500/20 border border-indigo-500/40 hover:bg-indigo-500/30 text-indigo-200 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <FileText size={14} />
              <span>Tailor Resume</span>
            </button>

            <button
              onClick={handlePrepareApply}
              disabled={isPreparing}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
            >
              {isPreparing ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
              <span>Prepare Apply</span>
            </button>
          </div>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          
          {/* A-G CareerOps Strategic Evaluation Report Card */}
          {agReport && (
            <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-500/[0.08] to-purple-500/[0.05] border border-indigo-500/30 space-y-4">
              <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
                  <Sparkles size={16} />
                  CareerOps A–G 7-Block Evaluation
                </h3>
                <span className="px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-200 text-xs font-mono font-bold">
                  {agReport.block_a_role?.archetype || 'Engineering'}
                </span>
              </div>

              {/* Block G Legitimacy Warning Badge */}
              {agReport.block_g_legitimacy && (
                <div className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
                  agReport.block_g_legitimacy.risk_level === 'HIGH' || agReport.block_g_legitimacy.is_scam
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                    : agReport.block_g_legitimacy.work_auth_blocked
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                }`}>
                  <span className="font-semibold">
                    🛡️ Block G Posting Legitimacy: {agReport.block_g_legitimacy.legitimacy_score}% ({agReport.block_g_legitimacy.risk_level} Risk)
                  </span>
                  {agReport.block_g_legitimacy.is_ghost_job && <span>👻 Ghost Job Flag</span>}
                  {agReport.block_g_legitimacy.work_auth_blocked && <span>🚫 Sponsorship Blocked</span>}
                </div>
              )}

              {/* Block B Skill Gaps & Mitigations */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-zinc-300">Block B: Skill Match & Gaps</div>
                <div className="flex flex-wrap gap-1.5">
                  {agReport.block_b_match?.matched_core_skills?.map((s: string, idx: number) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 text-xs font-mono">
                      ✓ {s}
                    </span>
                  ))}
                  {agReport.block_b_match?.hard_gaps?.map((g: string, idx: number) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30 text-xs font-mono">
                      ✕ {g}
                    </span>
                  ))}
                </div>
              </div>

              {/* Block C Seniority & Level Strategy */}
              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/10 text-xs text-zinc-300 space-y-1">
                <div className="font-semibold text-zinc-200">
                  Leveling Strategy ({agReport.block_c_level?.detected_level}):
                </div>
                <p className="text-zinc-400">{agReport.block_c_level?.positioning_angle}</p>
              </div>

              {/* Block F STAR+R Behavioral Interview Stories */}
              {agReport.block_f_interview_star?.star_behavioral_stories?.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-zinc-300">Block F: Recommended STAR+R Interview Story</div>
                  {agReport.block_f_interview_star.star_behavioral_stories.slice(0, 1).map((star: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-white/[0.02] border border-white/10 text-xs space-y-1.5">
                      <div className="font-semibold text-indigo-300">{star.competency}</div>
                      <div><strong className="text-zinc-400">Situation/Task:</strong> {star.situation} {star.task}</div>
                      <div><strong className="text-zinc-400">Action & Result:</strong> {star.action} <span className="text-emerald-400 font-semibold">{star.result}</span></div>
                      <div className="text-purple-300 italic"><strong className="text-zinc-400">Reflection:</strong> {star.reflection}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Audit / Fit Breakdown Section */}
          {job.match_reason && (
            <div className="p-4 rounded-xl bg-indigo-500/[0.06] border border-indigo-500/20 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
                <ShieldCheck size={14} />
                Audit Assessment & Rationale
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed">
                {job.match_reason}
              </p>
            </div>
          )}

          {/* Full Job Description */}
          <div>
            <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider mb-3">
              Job Description
            </h3>
            <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.05] text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap font-sans">
              {job.description || 'No detailed description available for this job posting.'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
