/* eslint-disable @typescript-eslint/no-explicit-any */
import { Job } from '../types';
import React, { useState, useEffect } from 'react';
import { Briefcase, CheckCircle, AlertCircle, Terminal, TrendingUp, Compass, Award, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { apiFetch } from '../utils/api';
import { motion } from 'framer-motion';

export default function Dashboard() {
  const { readiness, checkReadiness } = useAppStore();
  
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
    const interval = setInterval(fetchDashboardData, 20000);
    return () => clearInterval(interval);
  }, []);

  const topJobs = jobs
    .filter(j => j.match_score && j.match_score >= 8)
    .sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
    .slice(0, 3);

  const totalDiscovered = jobs.length;

  const kpis = [
    { label: 'Discovered', value: totalDiscovered, icon: Compass, color: 'text-blue-400' },
    { label: 'Tailored', value: stats.total_tailored || 0, icon: Award, color: 'text-purple-400' },
    { label: 'Applied', value: stats.total_applied || 0, icon: Briefcase, color: 'text-emerald-400' },
    { label: 'Interview', value: stats.total_interview || 0, icon: RefreshCw, color: 'text-amber-400' },
  ];

  // Animation variants
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16 pt-6 px-4 md:px-0">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Overview</h1>
          <p className="text-sm text-muted mt-2">High-level pipeline analytics and autonomous agent activity.</p>
        </div>
        <button onClick={fetchDashboardData} disabled={loading} className="btn-minimal flex items-center gap-2">
          <RefreshCw size={14} className={loading ? 'animate-spin text-blue-400' : 'text-gray-400'} />
          Sync Telemetry
        </button>
      </div>

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="space-y-8"
      >
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          {kpis.map((kpi, idx) => {
            const Icon = kpi.icon;
            return (
              <motion.div key={idx} variants={item} className="surface-panel p-5 flex flex-col justify-between h-32 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity duration-500 transform translate-x-4 -translate-y-4">
                   <Icon size={64} className={kpi.color} />
                </div>
                <div className="flex justify-between items-start relative z-10">
                  <span className="text-xs font-semibold text-muted uppercase tracking-wider">{kpi.label}</span>
                  <Icon size={18} className={kpi.color} />
                </div>
                <span className="text-4xl font-bold text-white relative z-10 font-sans tracking-tight">{kpi.value}</span>
              </motion.div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Core Stats */}
          <motion.div variants={item} className="surface-panel p-6 lg:col-span-2 space-y-8">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <TrendingUp size={18} className="text-emerald-400" />
              Conversion Metrics
            </h2>
            
            <div className="grid grid-cols-3 gap-6 border-b border-white/5 pb-8">
              <div>
                <div className="text-xs text-muted mb-2 uppercase tracking-wider font-semibold">Avg Match</div>
                <div className="text-2xl font-bold text-white">{stats.avg_score || 0.0}<span className="text-sm text-gray-500 font-normal">/10</span></div>
              </div>
              <div>
                <div className="text-xs text-muted mb-2 uppercase tracking-wider font-semibold">Response Rate</div>
                <div className="text-2xl font-bold text-white">{stats.response_rate || 0.0}<span className="text-sm text-gray-500 font-normal">%</span></div>
              </div>
              <div>
                <div className="text-xs text-muted mb-2 uppercase tracking-wider font-semibold">Top Source</div>
                <div className="text-lg font-bold text-white truncate">{stats.best_source || 'N/A'}</div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400 font-medium">Saved vs Discovered</span>
                  <span className="text-white font-semibold tracking-wide">{stats.total_saved || 0} / {totalDiscovered}</span>
                </div>
                <div className="h-2 w-full bg-[#18181b] rounded-full overflow-hidden shadow-inner">
                  <div className="h-full bg-gradient-to-r from-blue-600 to-cyan-400 shadow-[0_0_10px_rgba(56,189,248,0.5)]" style={{ width: `${totalDiscovered ? ((stats.total_saved || 0) / totalDiscovered) * 100 : 0}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400 font-medium">Applied vs Saved</span>
                  <span className="text-white font-semibold tracking-wide">{stats.total_applied || 0} / {stats.total_saved || 0}</span>
                </div>
                <div className="h-2 w-full bg-[#18181b] rounded-full overflow-hidden shadow-inner">
                  <div className="h-full bg-gradient-to-r from-emerald-600 to-teal-400 shadow-[0_0_10px_rgba(52,211,153,0.5)]" style={{ width: `${stats.total_saved ? ((stats.total_applied || 0) / stats.total_saved) * 100 : 0}%` }} />
                </div>
              </div>
            </div>
          </motion.div>

          {/* Readiness Checklist */}
          <motion.div variants={item} className="surface-panel p-6 space-y-6">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <CheckCircle size={18} className="text-blue-400" />
              System Status
            </h2>
            <div className="space-y-5">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <div className="flex items-center gap-3">
                  {readiness.ai_key ? <CheckCircle size={18} className="text-emerald-400" /> : <AlertCircle size={18} className="text-red-400" />}
                  <span className="text-sm font-medium text-gray-200">LLM Provider</span>
                </div>
                <span className={`text-[10px] px-2 py-1 rounded-md font-bold tracking-wider ${readiness.ai_key ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                  {readiness.ai_key ? 'ONLINE' : 'OFFLINE'}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <div className="flex items-center gap-3">
                  {readiness.resume ? <CheckCircle size={18} className="text-emerald-400" /> : <AlertCircle size={18} className="text-red-400" />}
                  <span className="text-sm font-medium text-gray-200">Base Resume</span>
                </div>
                <span className={`text-[10px] px-2 py-1 rounded-md font-bold tracking-wider ${readiness.resume ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                  {readiness.resume ? 'LOADED' : 'MISSING'}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <div className="flex items-center gap-3">
                  {readiness.identity ? <CheckCircle size={18} className="text-emerald-400" /> : <AlertCircle size={18} className="text-red-400" />}
                  <span className="text-sm font-medium text-gray-200">Identity Config</span>
                </div>
                <span className={`text-[10px] px-2 py-1 rounded-md font-bold tracking-wider ${readiness.identity ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                  {readiness.identity ? 'VERIFIED' : 'MISSING'}
                </span>
              </div>
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Activity Log */}
          <motion.div variants={item} className="surface-panel p-6 flex flex-col min-h-[320px]">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-white/5 pb-4 mb-4">
              <Terminal size={18} className="text-purple-400" />
              Recent Agent Activity
            </h2>
            <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar pr-2">
              {jobs.length === 0 ? (
                <div className="text-sm text-muted text-center py-10 flex flex-col items-center gap-2">
                  <Terminal size={24} className="opacity-20" />
                  No agent activity yet.
                </div>
              ) : (
                jobs.slice(0, 10).map((job, idx) => (
                  <div key={idx} className="text-sm text-gray-400 flex gap-4">
                    <span className="text-gray-500 shrink-0 font-mono text-xs mt-0.5">{new Date(job.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    <span className="leading-relaxed">Agent discovered <strong className="text-gray-200 font-medium">{job.title}</strong> role at <span className="text-blue-300">{job.company}</span></span>
                  </div>
                ))
              )}
            </div>
          </motion.div>

          {/* Top Matches */}
          <motion.div variants={item} className="surface-panel p-6 flex flex-col min-h-[320px]">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-white/5 pb-4 mb-4">
              <Award size={18} className="text-amber-400" />
              High Confidence Matches
            </h2>
            <div className="flex-1 space-y-3 overflow-y-auto custom-scrollbar pr-2">
              {topJobs.length === 0 ? (
                <div className="text-sm text-muted text-center py-10 flex flex-col items-center gap-2">
                  <Award size={24} className="opacity-20" />
                  No high-confidence matches found yet.
                </div>
              ) : (
                topJobs.map(job => (
                  <motion.div whileHover={{ scale: 1.01 }} key={job.id} className="list-card flex justify-between items-center group">
                    <div className="min-w-0 flex-1 pr-4">
                      <div className="text-sm font-semibold text-gray-100 truncate group-hover:text-blue-300 transition-colors">{job.title}</div>
                      <div className="text-xs text-gray-500 truncate mt-0.5">{job.company}</div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0 bg-black/20 px-3 py-1.5 rounded-full border border-white/5">
                      <span className="match-dot strong" />
                      <span className="text-xs font-bold text-emerald-400">{job.match_score}</span>
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
