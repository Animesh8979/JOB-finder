import React, { useEffect, useState } from 'react';
import {
  X,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  DollarSign,
  Zap,
  Sparkles,
  Loader2,
} from 'lucide-react';
import { apiFetch } from '../utils/api';
import type { JobViewV2 } from '../api/v2Client';

interface AtsBreakdownModalProps {
  job: JobViewV2;
  onClose: () => void;
  onOpenTailor?: (job: JobViewV2) => void;
}

interface AtsSimulationData {
  survival_score: number;
  keyword_coverage_pct: number;
  hard_disqualifiers: string[];
  matched_ngrams: string[];
  missing_ngrams: string[];
  action_verb_score: number;
  metric_quantifier_count: number;
  strong_verbs_found: string[];
  recommendations: string[];
}

interface SalaryArbitrageData {
  has_compensation: boolean;
  role_matched: string;
  offered_min?: number;
  offered_max?: number;
  offered_midpoint?: number;
  market_midpoint: number;
  compa_ratio?: number;
  market_tier: string;
  leverage_assessment: string;
  benchmarks: {
    title: string;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
  };
  geo_arbitrage_multiplier: number;
  currency: string;
}

export default function AtsBreakdownModal({ job, onClose, onOpenTailor }: AtsBreakdownModalProps) {
  const [atsData, setAtsData] = useState<AtsSimulationData | null>(null);
  const [salaryData, setSalaryData] = useState<SalaryArbitrageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [atsRes, salaryRes] = await Promise.allSettled([
          apiFetch(`/api/v2/jobs/${job.id}/ats_breakdown`)
            .then((r) => r.json() as Promise<AtsSimulationData>)
            .catch(() =>
              apiFetch(`/api/jobs/${job.id}/ats_breakdown`).then((r) => r.json() as Promise<AtsSimulationData>)
            ),
          apiFetch(`/api/v2/jobs/${job.id}/salary_arbitrage`)
            .then((r) => r.json() as Promise<SalaryArbitrageData>)
            .catch(() =>
              apiFetch(`/api/jobs/${job.id}/salary_arbitrage`).then((r) => r.json() as Promise<SalaryArbitrageData>)
            ),
        ]);

        if (!isMounted) return;

        if (atsRes.status === 'fulfilled') {
          setAtsData(atsRes.value);
        } else {
          setError('Failed to run ATS simulation.');
        }

        if (salaryRes.status === 'fulfilled') {
          setSalaryData(salaryRes.value);
        }
      } catch (err) {
        if (isMounted) setError(err instanceof Error ? err.message : 'Error running analysis');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [job.id]);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (score >= 60) return 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10';
    if (score >= 40) return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-[#0c0d14] border border-indigo-500/30 rounded-2xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9),0_0_40px_rgba(99,102,241,0.15)] flex flex-col overflow-hidden text-zinc-200 animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header Bar */}
        <div className="px-6 py-4 border-b border-white/[0.08] bg-white/[0.02] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-lg">
              <ShieldCheck size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold uppercase tracking-wider text-indigo-400">
                  Adversarial ATS Simulator
                </span>
                <span className="px-2 py-0.5 rounded-full bg-white/[0.06] text-[10px] font-mono text-zinc-400">
                  Taleo / Workday / Greenhouse Emulation
                </span>
              </div>
              <h2 className="text-base font-bold text-white leading-snug truncate max-w-lg">
                {job.title} <span className="text-zinc-500 font-normal">at {job.company}</span>
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors"
            title="Close (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center text-center gap-3 text-zinc-400">
              <Loader2 size={32} className="animate-spin text-indigo-400" />
              <p className="text-sm font-medium">Running N-Gram tokenization & ATS knockout audit...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
              {error}
            </div>
          ) : atsData && (
            <>
              {/* Top Metrics Row: Survival Score & Compa-Ratio */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Survival Probability */}
                <div className={`p-4 rounded-xl border flex flex-col justify-between ${getScoreColor(atsData.survival_score)}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold uppercase tracking-wider">ATS Pass Probability</span>
                    <Sparkles size={16} />
                  </div>
                  <div className="my-2">
                    <div className="text-4xl font-extrabold font-mono tracking-tight">
                      {atsData.survival_score}%
                    </div>
                    <p className="text-[11px] mt-1 opacity-80">
                      {atsData.survival_score >= 80 ? 'High probability of clearing automated filters' : 'At risk of automated rejection without keyword tuning'}
                    </p>
                  </div>
                  <div className="w-full bg-black/30 rounded-full h-1.5 overflow-hidden">
                    <div className="h-full bg-current transition-all duration-500" style={{ width: `${atsData.survival_score}%` }} />
                  </div>
                </div>

                {/* Keyword Density */}
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] flex flex-col justify-between">
                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="text-xs font-mono font-bold uppercase tracking-wider">Keyword Coverage</span>
                    <Zap size={16} className="text-indigo-400" />
                  </div>
                  <div className="my-2">
                    <div className="text-3xl font-bold font-mono text-white">
                      {atsData.keyword_coverage_pct}%
                    </div>
                    <p className="text-[11px] text-zinc-400 mt-1">
                      {atsData.matched_ngrams.length} matched / {atsData.missing_ngrams.length} missing terms
                    </p>
                  </div>
                  <span className="text-[10px] font-mono text-indigo-400">
                    N-Gram TF-IDF Frequency Verified
                  </span>
                </div>

                {/* Salary Compa-Ratio */}
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] flex flex-col justify-between">
                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="text-xs font-mono font-bold uppercase tracking-wider">Compa-Ratio Leverage</span>
                    <DollarSign size={16} className="text-emerald-400" />
                  </div>
                  <div className="my-2">
                    <div className="text-3xl font-bold font-mono text-emerald-400">
                      {salaryData?.compa_ratio ? `${salaryData.compa_ratio}%` : 'Unlisted'}
                    </div>
                    <p className="text-[11px] text-zinc-400 mt-1 truncate">
                      {salaryData?.market_tier || 'No explicit salary band published'}
                    </p>
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500">
                    Benchmark: P50 ${salaryData?.market_midpoint?.toLocaleString() || '155,000'}
                  </span>
                </div>
              </div>

              {/* Hard Knockouts Banner */}
              {atsData.hard_disqualifiers.length > 0 && (
                <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-start gap-3 text-rose-300">
                  <AlertTriangle size={20} className="shrink-0 mt-0.5 text-rose-400" />
                  <div className="space-y-1">
                    <h4 className="text-xs font-bold uppercase tracking-wider font-mono">
                      Hard Knockout Disqualifiers Detected
                    </h4>
                    <p className="text-xs opacity-90">
                      The ATS will immediately drop candidate profiles lacking explicit verification for:
                    </p>
                    <ul className="list-disc list-inside text-xs font-medium space-y-0.5 pt-1">
                      {atsData.hard_disqualifiers.map((dq, i) => (
                        <li key={i}>{dq}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Missing vs Matched N-Grams Matrix */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Missing Keywords */}
                <div className="p-4 rounded-xl bg-rose-950/10 border border-rose-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                      <AlertTriangle size={14} /> Missing High-Impact N-Grams ({atsData.missing_ngrams.length})
                    </h4>
                    <span className="text-[10px] text-zinc-500">Inject into tailored CV</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto custom-scrollbar p-1">
                    {atsData.missing_ngrams.map((term, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-300 text-xs font-mono"
                      >
                        + {term}
                      </span>
                    ))}
                    {atsData.missing_ngrams.length === 0 && (
                      <span className="text-xs text-zinc-500 italic">No critical keywords missing!</span>
                    )}
                  </div>
                </div>

                {/* Matched Keywords */}
                <div className="p-4 rounded-xl bg-emerald-950/10 border border-emerald-500/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 size={14} /> Verified Matched Keywords ({atsData.matched_ngrams.length})
                    </h4>
                    <span className="text-[10px] text-zinc-500">Already in resume</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto custom-scrollbar p-1">
                    {atsData.matched_ngrams.map((term, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs font-mono"
                      >
                        ✓ {term}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recommendations Box */}
              {atsData.recommendations.length > 0 && (
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-2">
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                    <TrendingUp size={14} className="text-indigo-400" />
                    Adversarial ATS Pass Strategy
                  </h4>
                  <ul className="space-y-1 text-xs text-zinc-300">
                    {atsData.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-indigo-400 font-bold">•</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Negotiation Assessment */}
              {salaryData?.has_compensation && (
                <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-950/20 to-indigo-950/20 border border-emerald-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
                  <div>
                    <span className="text-emerald-400 font-bold font-mono uppercase tracking-wider text-[10px]">
                      Compensation Negotiation Assessment
                    </span>
                    <p className="text-zinc-300 mt-0.5">{salaryData.leverage_assessment}</p>
                  </div>
                  {salaryData.geo_arbitrage_multiplier > 1.0 && (
                    <div className="px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-mono text-[11px] shrink-0">
                      +{Math.round((salaryData.geo_arbitrage_multiplier - 1) * 100)}% Geo-Arbitrage Power
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-white/[0.08] bg-white/[0.02] flex items-center justify-between shrink-0">
          <div className="text-[11px] text-zinc-500 font-mono">
            Press <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-zinc-300 font-bold">Esc</kbd> to close • <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-zinc-300 font-bold">A</kbd> to tailor
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors"
            >
              Dismiss
            </button>
            {onOpenTailor && (
              <button
                onClick={() => {
                  onClose();
                  onOpenTailor(job);
                }}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 transition-all"
              >
                <Sparkles size={14} />
                Auto-Tailor to Close Gaps
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
