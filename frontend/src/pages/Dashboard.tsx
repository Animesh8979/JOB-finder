/* eslint-disable @typescript-eslint/no-explicit-any */
import { Job } from '../types';
import React, { useState, useEffect } from 'react';
import { Briefcase, CheckCircle, AlertCircle, Terminal, TrendingUp, Compass, Award, RefreshCw, Zap, ArrowUpRight, Clock, Shield, User, Link2 } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { apiFetch } from '../utils/api';
import { motion } from 'framer-motion';
import HeroGreeting from '../components/HeroGreeting';
import LiveTicker from '../components/LiveTicker';
import MagneticButton from '../components/MagneticButton';

function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const duration = 800;
    const start = performance.now();
    const from = display;
    const step = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(from + (value - from) * eased));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
  return <>{display}{suffix}</>;
}

export default function Dashboard() {
  const { readiness, checkReadiness, recruiterScore, fetchRecruiterScore, profile, fetchProfile } = useAppStore();
  
  const [stats, setStats] = useState<any>({
    total_saved: 0,
    total_tailored: 0,
    total_applied: 0,
    total_interview: 0,
    total_offer: 0,
    total_rejected: 0,
    avg_score: 0,
    response_rate: 0,
    best_source: 'N/A'
  });
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);

  async function fetchDashboardData() {
    setLoading(true);
    try {
      const statsRes = await apiFetch('/api/stats', { showToastOnError: false });
      if (statsRes.ok) setStats(await statsRes.json());

      const jobsRes = await apiFetch('/api/jobs', { showToastOnError: false });
      if (jobsRes.ok) setJobs(await jobsRes.json());

      await checkReadiness();
    } catch (e: any) {
      console.error('Failed to load dashboard telemetry:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDashboardData();
    if (!recruiterScore.loaded && !recruiterScore.loading) fetchRecruiterScore();
    if (!profile) fetchProfile();
    const interval = setInterval(fetchDashboardData, 20000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const topJobs = jobs
    .filter(j => j.match_score && j.match_score >= 8)
    .sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
    .slice(0, 5);

  const totalDiscovered = jobs.length;

  const kpis = [
    { label: 'Discovered', value: totalDiscovered, icon: Compass, gradient: 'from-indigo-500/15 to-blue-500/15', iconColor: 'text-indigo-400', borderGlow: 'hover:shadow-indigo-500/10' },
    { label: 'Tailored', value: stats.total_tailored || 0, icon: Award, gradient: 'from-purple-500/15 to-pink-500/15', iconColor: 'text-purple-400', borderGlow: 'hover:shadow-purple-500/10' },
    { label: 'Applied', value: stats.total_applied || 0, icon: Briefcase, gradient: 'from-emerald-500/15 to-teal-500/15', iconColor: 'text-emerald-400', borderGlow: 'hover:shadow-emerald-500/10' },
    { label: 'Interview', value: stats.total_interview || 0, icon: Zap, gradient: 'from-amber-500/15 to-orange-500/15', iconColor: 'text-amber-400', borderGlow: 'hover:shadow-amber-500/10' },
  ];

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08, delayChildren: 0.1 }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20, filter: 'blur(4px)' },
    show: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { type: 'spring' as const, stiffness: 300, damping: 28 } }
  };

  return (
    <div className="space-y-6 max-w-[1200px] mx-auto pb-16 pt-4 px-2 md:px-0">
      {/* Cinematic Hero */}
      <HeroGreeting
        agentOnline={Boolean(readiness.ai_key)}
        jobCount={totalDiscovered}
        bestScoreCount={topJobs.length}
      />

      {/* Live data ticker */}
      <LiveTicker
        fallback={[
          { label: 'agent', value: readiness.ai_key ? 'online' : 'idle', tone: readiness.ai_key ? 'ok' : 'warn' },
          { label: 'tracked', value: totalDiscovered },
          { label: 'tailored', value: stats.total_tailored || 0 },
          { label: 'applied', value: stats.total_applied || 0, tone: 'accent' },
          { label: 'interviews', value: stats.total_interview || 0, tone: 'warn' },
          { label: 'offers', value: stats.total_offer || 0, tone: 'ok' },
        ]}
      />

      {/* ═══════════════════════════════════════════════
          ATS RESUME HEALTH — Verified Profile Card
         ═══════════════════════════════════════════════ */}
      {(profile || recruiterScore.data) && (
        <motion.div
          initial={{ opacity: 0, y: 20, filter: 'blur(4px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ type: 'spring', stiffness: 250, damping: 28, delay: 0.15 }}
          className="surface-panel p-6 md:p-8 space-y-6"
        >
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/15 to-purple-500/15">
                <Shield size={18} className="text-indigo-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white tracking-tight">ATS Resume Health</h2>
                <p className="text-[10px] text-zinc-500 font-medium tracking-wider uppercase">
                  HackerRank hiring-agent taxonomy · Rule-based · Zero LLM cost
                </p>
              </div>
            </div>
            <MagneticButton
              onClick={() => { fetchRecruiterScore(); }}
              disabled={recruiterScore.loading}
              className="btn-minimal flex items-center gap-2 text-xs"
            >
              <RefreshCw size={13} className={recruiterScore.loading ? 'animate-spin text-indigo-400' : 'text-zinc-500'} />
              Re-scan
            </MagneticButton>
          </div>

          {/* Profile Identity Strip */}
          {profile && (
            <div className="flex flex-wrap items-center gap-4 px-4 py-3 rounded-xl bg-white/[0.015] border border-white/[0.04]">
              <div className="flex items-center gap-2 text-sm">
                <User size={14} className="text-zinc-500" />
                <span className="text-zinc-200 font-medium">{profile.name || 'Unknown'}</span>
              </div>
              {profile.email && (
                <div className="text-xs text-zinc-500">{profile.email}</div>
              )}
              {profile.links?.github && (
                <div className="flex items-center gap-1.5 text-xs text-indigo-400/80">
                  <Link2 size={12} />
                  <span>{profile.links.github.replace('https://github.com/', '@')}</span>
                </div>
              )}
              <div className="ml-auto flex items-center gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold tracking-wider">
                  {(profile.skills || []).length} SKILLS
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold tracking-wider">
                  {(profile.experience || []).length} ROLES
                </span>
              </div>
            </div>
          )}

          {/* Score Body */}
          {recruiterScore.loading && (
            <div className="text-center py-8">
              <motion.div
                animate={{ opacity: [0.3, 0.6] }}
                transition={{ duration: 0.8, repeat: Infinity, ease: 'easeInOut' }}
                className="text-sm text-indigo-300"
              >
                Scoring resume against HackerRank taxonomy...
              </motion.div>
            </div>
          )}

          {recruiterScore.data && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left: Score Gauge + Summary */}
              <div className="flex flex-col items-center justify-center gap-4">
                {/* Radial gauge */}
                <div className="relative w-32 h-32">
                  <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                    <circle cx="18" cy="18" r="15.9155" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="2.5" />
                    <motion.circle
                      cx="18" cy="18" r="15.9155" fill="none"
                      stroke="url(#atsGrad)"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeDasharray="100"
                      initial={{ strokeDashoffset: 100 }}
                      animate={{ strokeDashoffset: 100 - Math.min(100, (recruiterScore.data.total / 120) * 100) }}
                      transition={{ duration: 1.2, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
                    />
                    <defs>
                      <linearGradient id="atsGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#6366f1" />
                        <stop offset="100%" stopColor="#a855f7" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-bold text-white tracking-tight">
                      <AnimatedCounter value={recruiterScore.data.total} />
                    </span>
                    <span className="text-[10px] text-zinc-500 font-semibold tracking-wider">/ 120</span>
                  </div>
                </div>

                {/* Bonus & Deduction pills */}
                <div className="flex items-center gap-3 text-xs">
                  <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                    +{recruiterScore.data.bonus} bonus
                  </span>
                  <span className="px-2.5 py-1 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold">
                    {recruiterScore.data.deduction} deduction
                  </span>
                </div>
              </div>

              {/* Center: Category Breakdown */}
              <div className="space-y-4">
                <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-[0.15em]">Category Breakdown</h3>
                {[
                  { key: 'open_source', label: 'Open Source', max: 35, color: 'from-cyan-500 to-blue-500', glow: 'rgba(6,182,212,0.4)' },
                  { key: 'self_projects', label: 'Self Projects', max: 30, color: 'from-purple-500 to-pink-500', glow: 'rgba(168,85,247,0.4)' },
                  { key: 'production', label: 'Production', max: 25, color: 'from-emerald-500 to-teal-400', glow: 'rgba(52,211,153,0.4)' },
                  { key: 'technical_skills', label: 'Technical Skills', max: 10, color: 'from-amber-500 to-orange-400', glow: 'rgba(251,191,36,0.4)' },
                ].map(cat => {
                  const val = recruiterScore.data!.by_category[cat.key] || 0;
                  const pct = Math.min(100, (val / cat.max) * 100);
                  return (
                    <div key={cat.key}>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-zinc-400 font-medium">{cat.label}</span>
                        <span className="text-zinc-300 font-bold text-xs-mono">{val} / {cat.max}</span>
                      </div>
                      <div className="h-1.5 w-full bg-zinc-800/60 rounded-full overflow-hidden">
                        <motion.div
                          className={`h-full rounded-full bg-gradient-to-r ${cat.color}`}
                          style={{ boxShadow: `0 0 12px ${cat.glow}` }}
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 1, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Right: Per-Rule Rationale */}
              <div className="space-y-2 max-h-[260px] overflow-y-auto custom-scrollbar pr-1">
                <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-[0.15em] sticky top-0 bg-transparent pb-1">Rule Rationale</h3>
                {recruiterScore.data.rationale.map((rule: any, idx: number) => {
                  const isPositive = rule.delta > 0;
                  return (
                    <motion.div
                      key={`${rule.rule}-${idx}`}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.06 + 0.5 }}
                      className={`flex items-start gap-2.5 px-3 py-2 rounded-lg text-xs ${
                        isPositive
                          ? 'bg-emerald-500/[0.06] border border-emerald-500/10'
                          : 'bg-rose-500/[0.06] border border-rose-500/10'
                      }`}
                    >
                      <span className={`font-mono font-bold shrink-0 w-8 text-right ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {rule.delta > 0 ? `+${rule.delta}` : rule.delta}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className={`leading-relaxed ${isPositive ? 'text-emerald-200/80' : 'text-rose-200/80'}`}>
                          {rule.note}
                        </div>
                        <div className="text-[9px] text-zinc-600 mt-0.5 capitalize">{rule.category.replace(/_/g, ' ')}</div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Header */}
      <div className="flex items-end justify-between px-1">
        <div>
          <h2 className="text-xl md:text-2xl font-semibold text-white tracking-tight">Pipeline analytics</h2>
          <p className="text-xs text-zinc-500 mt-1 font-medium">Real-time activity across discovery & application</p>
        </div>
        <MagneticButton onClick={fetchDashboardData} disabled={loading} className="btn-minimal flex items-center gap-2 text-xs">
          <RefreshCw size={13} className={loading ? 'animate-spin text-indigo-400' : 'text-zinc-500'} />
          Sync
        </MagneticButton>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          {kpis.map((kpi, idx) => {
            const Icon = kpi.icon;
            return (
              <motion.div 
                key={idx} 
                variants={item} 
                className={`surface-panel p-5 flex flex-col justify-between h-[130px] relative overflow-hidden group ${kpi.borderGlow}`}
              >
                {/* Background gradient blob */}
                <div className={`absolute -top-6 -right-6 w-24 h-24 rounded-full bg-gradient-to-br ${kpi.gradient} blur-2xl opacity-50 group-hover:opacity-80 transition-opacity duration-700`} />
                
                <div className="flex justify-between items-start relative z-10">
                  <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-[0.15em]">{kpi.label}</span>
                  <div className={`p-1.5 rounded-lg bg-gradient-to-br ${kpi.gradient}`}>
                    <Icon size={14} className={kpi.iconColor} />
                  </div>
                </div>
                <span className="text-3xl md:text-4xl font-bold text-white relative z-10 tracking-tight stat-value">
                  <AnimatedCounter value={kpi.value} />
                </span>
              </motion.div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Conversion Metrics */}
          <motion.div variants={item} className="surface-panel p-6 lg:col-span-2 space-y-6">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <TrendingUp size={16} className="text-emerald-400" />
              Conversion Funnel
            </h2>
            
            <div className="grid grid-cols-3 gap-6 border-b border-white/[0.04] pb-6">
              <div>
                <div className="text-[10px] text-zinc-500 mb-2 uppercase tracking-[0.15em] font-semibold">Avg Match</div>
                <div className="text-2xl font-bold text-white">
                  <AnimatedCounter value={Math.round((stats.avg_score || 0) * 10) / 10} />
                  <span className="text-sm text-zinc-600 font-normal ml-0.5">/10</span>
                </div>
              </div>
              <div>
                <div className="text-[10px] text-zinc-500 mb-2 uppercase tracking-[0.15em] font-semibold">Response Rate</div>
                <div className="text-2xl font-bold text-white">
                  <AnimatedCounter value={stats.response_rate || 0} suffix="%" />
                </div>
              </div>
              <div>
                <div className="text-[10px] text-zinc-500 mb-2 uppercase tracking-[0.15em] font-semibold">Top Source</div>
                <div className="text-base font-bold text-white truncate mt-1">{stats.best_source || 'N/A'}</div>
              </div>
            </div>

            <div className="space-y-5">
              <div>
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-zinc-500 font-medium">Saved / Discovered</span>
                  <span className="text-zinc-300 font-semibold tracking-wide text-xs-mono">{stats.total_saved || 0} / {totalDiscovered}</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800/60 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400" 
                    style={{ boxShadow: '0 0 12px rgba(99, 102, 241, 0.4)' }}
                    initial={{ width: 0 }}
                    animate={{ width: `${totalDiscovered ? ((stats.total_saved || 0) / totalDiscovered) * 100 : 0}%` }}
                    transition={{ duration: 1, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-zinc-500 font-medium">Applied / Saved</span>
                  <span className="text-zinc-300 font-semibold tracking-wide text-xs-mono">{stats.total_applied || 0} / {stats.total_saved || 0}</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800/60 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400"
                    style={{ boxShadow: '0 0 12px rgba(52, 211, 153, 0.4)' }}
                    initial={{ width: 0 }}
                    animate={{ width: `${stats.total_saved ? ((stats.total_applied || 0) / stats.total_saved) * 100 : 0}%` }}
                    transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-zinc-500 font-medium">Interview / Applied</span>
                  <span className="text-zinc-300 font-semibold tracking-wide text-xs-mono">{stats.total_interview || 0} / {stats.total_applied || 0}</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800/60 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full rounded-full bg-gradient-to-r from-amber-500 to-orange-400"
                    style={{ boxShadow: '0 0 12px rgba(251, 191, 36, 0.4)' }}
                    initial={{ width: 0 }}
                    animate={{ width: `${stats.total_applied ? ((stats.total_interview || 0) / stats.total_applied) * 100 : 0}%` }}
                    transition={{ duration: 1, delay: 0.7, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
              </div>
            </div>
          </motion.div>

          {/* System Status */}
          <motion.div variants={item} className="surface-panel p-6 space-y-5">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <CheckCircle size={16} className="text-indigo-400" />
              System Status
            </h2>
            <div className="space-y-3">
              {[
                { label: 'LLM Provider', ok: readiness.ai_key, okText: 'ONLINE', failText: 'OFFLINE' },
                { label: 'Base Resume', ok: readiness.resume, okText: 'LOADED', failText: 'MISSING' },
                { label: 'Identity Config', ok: readiness.identity, okText: 'VERIFIED', failText: 'MISSING' },
              ].map(s => (
                <div key={s.label} className="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.015] border border-white/[0.04] group hover:border-white/[0.08] transition-all">
                  <div className="flex items-center gap-3">
                    {s.ok 
                      ? <CheckCircle size={16} className="text-emerald-400" /> 
                      : <AlertCircle size={16} className="text-zinc-600" />
                    }
                    <span className="text-sm font-medium text-zinc-300">{s.label}</span>
                  </div>
                  <span className={`text-[9px] px-2.5 py-1 rounded-md font-bold tracking-[0.1em] ${
                    s.ok 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'bg-zinc-800/50 text-zinc-600 border border-zinc-700/30'
                  }`}>
                    {s.ok ? s.okText : s.failText}
                  </span>
                </div>
              ))}
            </div>

            {/* Quick Stats */}
            <div className="pt-4 border-t border-white/[0.04] space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-500">Offers</span>
                <span className="text-emerald-400 font-bold">{stats.total_offer || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-500">Rejected</span>
                <span className="text-zinc-500 font-bold">{stats.total_rejected || 0}</span>
              </div>
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Activity Feed */}
          <motion.div variants={item} className="surface-panel p-6 flex flex-col min-h-[340px]">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-white/[0.04] pb-4 mb-4">
              <Terminal size={16} className="text-purple-400" />
              Agent Activity
              {jobs.length > 0 && (
                <span className="ml-auto text-[10px] text-zinc-600 font-medium tracking-wider">{jobs.length} events</span>
              )}
            </h2>
            <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar pr-2">
              {jobs.length === 0 ? (
                <div className="text-sm text-zinc-600 text-center py-14 flex flex-col items-center gap-3">
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                    <Terminal size={20} className="text-zinc-700" />
                  </div>
                  <span className="text-xs font-medium">No agent activity yet</span>
                  <span className="text-[10px] text-zinc-700">Run a job search to see results here</span>
                </div>
              ) : (
                jobs.slice(0, 12).map((job, idx) => (
                  <motion.div 
                    key={idx} 
                    className="text-sm text-zinc-500 flex gap-3 py-1 group"
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                  >
                    <div className="flex flex-col items-center gap-1 shrink-0 pt-0.5">
                      <Clock size={12} className="text-zinc-700" />
                      <div className="w-px flex-1 bg-zinc-800/50" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="leading-relaxed">
                        <span className="text-zinc-400">Discovered </span>
                        <strong className="text-zinc-200 font-medium">{job.title}</strong>
                        <span className="text-zinc-500"> at </span>
                        <span className="text-indigo-300/80">{job.company}</span>
                      </div>
                      <div className="text-[10px] text-zinc-600 mt-0.5 font-mono">
                        {new Date(job.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </div>
                    </div>
                    {job.match_score && job.match_score >= 8 && (
                      <div className="shrink-0 flex items-center">
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                          {job.match_score}
                        </span>
                      </div>
                    )}
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>

          {/* Top Matches */}
          <motion.div variants={item} className="surface-panel p-6 flex flex-col min-h-[340px]">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-white/[0.04] pb-4 mb-4">
              <Award size={16} className="text-amber-400" />
              High Confidence Matches
              {topJobs.length > 0 && (
                <span className="ml-auto text-[10px] text-zinc-600 font-medium tracking-wider">Top {topJobs.length}</span>
              )}
            </h2>
            <div className="flex-1 space-y-2 overflow-y-auto custom-scrollbar pr-2">
              {topJobs.length === 0 ? (
                <div className="text-sm text-zinc-600 text-center py-14 flex flex-col items-center gap-3">
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                    <Award size={20} className="text-zinc-700" />
                  </div>
                  <span className="text-xs font-medium">No high-confidence matches yet</span>
                  <span className="text-[10px] text-zinc-700">Matches scoring 8+ appear here</span>
                </div>
              ) : (
                topJobs.map((job, idx) => (
                  <motion.div 
                    whileHover={{ scale: 1.01, x: 4 }} 
                    key={job.id} 
                    className="list-card flex justify-between items-center group"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.08 }}
                  >
                    <div className="min-w-0 flex-1 pr-4">
                      <div className="text-sm font-semibold text-zinc-200 truncate group-hover:text-indigo-300 transition-colors">{job.title}</div>
                      <div className="text-[11px] text-zinc-600 truncate mt-0.5 flex items-center gap-1.5">
                        {job.company}
                        <ArrowUpRight size={10} className="text-zinc-700 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="flex items-center gap-2 bg-emerald-500/8 px-3 py-1.5 rounded-lg border border-emerald-500/15">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]" />
                        <span className="text-xs font-bold text-emerald-400">{job.match_score}</span>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
