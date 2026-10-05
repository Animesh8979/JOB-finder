import React, { useState, useEffect, useMemo, lazy, Suspense, useCallback } from 'react';
import {
  Briefcase,
  BarChart3,
  Settings,
  RefreshCw,
  Target,
  Inbox,
  Globe,
  Gauge,
  Award,
  Zap,
  Shield,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  Wand2,
} from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { listJobsV2, listRunsV2, subscribeToRunsV2, type JobViewV2, type RunViewV2 } from '../api/v2Client';
import { useAppStore } from '../store/useAppStore';
import { apiFetch } from '../utils/api';
import CommandBar from '../components/CommandBar';
import LiveIntelFeed from '../components/LiveIntelFeed';
import LiveAgentConsole from '../components/LiveAgentConsole';
import PipelineStatusPanel from '../components/PipelineStatusPanel';
import FunnelPanel from '../components/FunnelPanel';
import RecruiterScoreCard from '../components/RecruiterScoreCard';

const JobDetailDrawer = lazy(() => import('../components/JobDetailDrawer'));
const TailorDrawer = lazy(() => import('../components/TailorDrawer'));
const PrepareApplyDrawer = lazy(() => import('../components/PrepareApplyDrawer'));
const SettingsDrawer = lazy(() => import('../components/SettingsDrawer'));
const SkillsLibraryPanel = lazy(() => import('../components/SkillsLibraryPanel'));
const AtsBreakdownModal = lazy(() => import('../components/AtsBreakdownModal'));
const ApexWarfareCenter = lazy(() => import('../components/ApexWarfareCenter'));

function DrawerFallback() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-8 h-8 rounded-full border-2 border-indigo-500/30 border-t-indigo-400 animate-spin" />
    </div>
  );
}

/* ── Navigation Tabs ── */
type TabId = 'warfare' | 'jobs' | 'analytics' | 'pipeline' | 'skills';
const TABS: { id: TabId; label: string; icon: React.ElementType; badge?: string }[] = [
  { id: 'warfare', label: 'Apex Warfare Engine', icon: Shield, badge: 'v2' },
  { id: 'jobs', label: 'Job Matches', icon: Briefcase },
  { id: 'analytics', label: 'ATS & Analytics', icon: BarChart3 },
  { id: 'pipeline', label: 'Pipeline Engine', icon: Settings },
  { id: 'skills', label: 'Agent Playbooks', icon: Zap },
];

/* ── Top Header Bar ── */
function HeaderBar({
  name,
  jobCount,
  strongCount,
  atsScore,
  activeTab,
  onSelectTab,
  onRefresh,
  onOpenSettings,
}: {
  name: string;
  jobCount: number;
  strongCount: number;
  atsScore?: number;
  activeTab: TabId;
  onSelectTab: (tab: TabId) => void;
  onRefresh: () => void;
  onOpenSettings: () => void;
}) {
  const hour = new Date().getHours();
  const greeting = hour < 5 ? 'Up late' : hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : hour < 21 ? 'Good evening' : 'Quiet night';

  return (
    <header className="p-3.5 md:p-4 rounded-2xl bg-[#0d0d12]/90 border border-white/[0.08] shadow-[0_4px_24px_rgba(0,0,0,0.4)] flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
      {/* Brand & Candidate Info */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
          <Briefcase size={20} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg md:text-xl font-bold text-white tracking-tight">
              {greeting}, <span className="text-gradient-primary">{name}</span>
            </h1>
            {atsScore != null && (
              <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-xs font-mono font-bold">
                <Shield size={11} className="text-indigo-400" /> ATS {atsScore}/120
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-[11px] text-zinc-400 mt-0.5">
            <span className="flex items-center gap-1 text-zinc-300 font-medium">
              <Inbox size={11} /> {jobCount} jobs
            </span>
            <span className="flex items-center gap-1 text-emerald-400 font-medium">
              <Target size={11} /> {strongCount} strong fits
            </span>
            <span className="flex items-center gap-1.5 text-zinc-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Cockpit Active
            </span>
          </div>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex items-center gap-1 bg-black/40 p-1 rounded-xl border border-white/[0.06] overflow-x-auto self-stretch md:self-auto">
        {TABS.map((t, idx) => {
          const Icon = t.icon;
          const active = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => onSelectTab(t.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all relative shrink-0 ${
                active
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]'
              }`}
            >
              <Icon size={14} />
              <span>{t.label}</span>
              {t.badge && (
                <span className="px-1.5 py-0.2 rounded-full bg-white/20 text-[10px] font-mono">
                  {t.badge}
                </span>
              )}
              <kbd className="hidden lg:inline text-[9px] opacity-60 font-mono ml-0.5">
                {idx + 1}
              </kbd>
            </button>
          );
        })}
      </div>

      {/* Global Actions */}
      <div className="hidden xl:flex items-center gap-2">
        <button
          onClick={onRefresh}
          className="p-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.06] text-zinc-400 hover:text-white transition-colors"
          title="Refresh All Data"
        >
          <RefreshCw size={14} />
        </button>
        <button
          onClick={onOpenSettings}
          className="p-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.06] text-zinc-400 hover:text-white transition-colors"
          title="Engine Settings"
        >
          <Settings size={14} />
        </button>
      </div>
    </header>
  );
}

/* ── Lightweight Stats Strip ── */
function StatsStrip({ vals }: { vals: Record<string, number> }) {
  const items = [
    { key: 'total', label: 'Pipeline Total', icon: Inbox, color: 'text-indigo-400' },
    { key: 'strong', label: 'Strong Fits (>=75%)', icon: Target, color: 'text-emerald-400' },
    { key: 'avg', label: 'Average Match', icon: Gauge, color: 'text-violet-400', suffix: '%' },
    { key: 'remote', label: 'Remote Ratio', icon: Globe, color: 'text-sky-400', suffix: '%' },
    { key: 'tailored', label: 'Tailored Resumes', icon: Award, color: 'text-purple-400' },
    { key: 'interviews', label: 'Interviews Scheduled', icon: Zap, color: 'text-amber-400' },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 shrink-0">
      {items.map((item) => {
        const Icon = item.icon;
        const v = vals[item.key] ?? 0;
        return (
          <div
            key={item.key}
            className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] flex items-center gap-3 hover:bg-white/[0.03] transition-colors"
          >
            <div className="w-8 h-8 rounded-lg bg-white/[0.03] border border-white/[0.06] flex items-center justify-center shrink-0">
              <Icon size={15} className={item.color} />
            </div>
            <div className="min-w-0">
              <div className="text-base font-bold text-white font-mono leading-tight tabnum">
                {v}
                {'suffix' in item ? item.suffix : ''}
              </div>
              <div className="text-[9px] uppercase tracking-wider text-zinc-500 truncate">
                {item.label}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── ATS Health Overview Card (with Autonomous Upgrade action) ── */
function ATSOverviewCard({ onUpgradeClick, isUpgrading }: { onUpgradeClick: () => void; isUpgrading: boolean }) {
  const { recruiterScore, fetchRecruiterScore, profile } = useAppStore();

  useEffect(() => {
    if (!recruiterScore.loaded && !recruiterScore.loading) fetchRecruiterScore();
  }, [recruiterScore.loaded, recruiterScore.loading, fetchRecruiterScore]);

  if (!recruiterScore.data) {
    return (
      <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.06] text-center text-zinc-500">
        <RefreshCw size={20} className="animate-spin text-indigo-400 mx-auto mb-2" />
        <p className="text-xs">Evaluating resume against HackerRank recruiter rubrics...</p>
      </div>
    );
  }

  const r = recruiterScore.data;
  const pct = Math.min(100, (r.total / 120) * 100);

  const categories = [
    { key: 'open_source', label: 'Open Source', max: 35, color: 'from-cyan-400 to-blue-500' },
    { key: 'self_projects', label: 'Independent Projects', max: 30, color: 'from-purple-400 to-fuchsia-500' },
    { key: 'production', label: 'Production Experience', max: 25, color: 'from-emerald-400 to-teal-500' },
    { key: 'technical_skills', label: 'Core Technical Skills', max: 10, color: 'from-amber-400 to-orange-500' },
  ];

  return (
    <div className="p-5 md:p-6 rounded-2xl bg-gradient-to-br from-indigo-950/30 to-purple-950/15 border border-indigo-500/20 flex flex-col justify-between gap-6 shadow-[0_4px_30px_rgba(0,0,0,0.3)]">
      <div>
        {/* Top Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Shield size={16} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">ATS Recruiter Health</h3>
              <p className="text-xs text-zinc-400">HackerRank taxonomy scoring (0–120 scale)</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-mono font-bold">
            <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
              +{r.bonus} bonus
            </span>
            <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/25">
              {r.deduction} penalty
            </span>
          </div>
        </div>

        {/* Gauge & Category Bars */}
        <div className="mt-6 flex flex-col md:flex-row items-center gap-6">
          {/* Circular Gauge */}
          <div className="relative w-28 h-28 shrink-0">
            <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
              <circle
                cx="18"
                cy="18"
                r="15.9"
                fill="none"
                stroke="url(#gaugeGradient)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray="100"
                strokeDashoffset={100 - pct}
                className="transition-[stroke-dashoffset] duration-1000 ease-out"
              />
              <defs>
                <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="50%" stopColor="#a855f7" />
                  <stop offset="100%" stopColor="#ec4899" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-white font-mono leading-none">{r.total}</span>
              <span className="text-[10px] text-zinc-500 font-bold tracking-wider mt-0.5">/ 120</span>
            </div>
          </div>

          {/* Category Progress Bars */}
          <div className="flex-1 w-full space-y-3">
            {categories.map((c) => {
              const val = r.by_category[c.key] || 0;
              const catPct = Math.min(100, (val / c.max) * 100);
              return (
                <div key={c.key} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-zinc-400 font-medium">{c.label}</span>
                    <span className="font-mono text-zinc-300 font-semibold">
                      {val} / {c.max} pts
                    </span>
                  </div>
                  <div className="h-2 bg-zinc-800/60 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${c.color} transition-all duration-700`}
                      style={{ width: `${catPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Autonomous Upgrade Action */}
      <div className="pt-4 border-t border-white/[0.06] flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-xs text-zinc-400 leading-relaxed text-center sm:text-left">
          Resume: <span className="text-white font-medium">{profile?.name || 'Candidate'}</span> · Target: Business Analyst / Data Analyst
        </p>
        <button
          onClick={onUpgradeClick}
          disabled={isUpgrading}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50 shrink-0"
        >
          <Wand2 size={14} className={isUpgrading ? 'animate-spin' : ''} />
          <span>{isUpgrading ? 'Auditing & Upgrading...' : '1-Click Autonomous Resume Upgrade'}</span>
        </button>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════
   COMMAND CENTER — Master Dashboard
   ══════════════════════════════════════════ */
export default function CommandCenter() {
  const queryClient = useQueryClient();
  const { profile, fetchProfile, fetchRecruiterScore } = useAppStore();

  const [activeTab, setActiveTab] = useState<TabId>('jobs');
  const [extraStats, setExtraStats] = useState({ tailored: 0, interviews: 0 });
  const [filters, setFilters] = useState({ remoteOnly: false, minScore: 0, searchQuery: '' });
  const [jobPage, setJobPage] = useState(1);
  const [isUpgradingResume, setIsUpgradingResume] = useState(false);

  const [selectedJob, setSelectedJob] = useState<JobViewV2 | null>(null);
  const [activeDrawer, setActiveDrawer] = useState<'none' | 'detail' | 'tailor' | 'prepare' | 'setup' | 'ats'>('none');
  const [activeRunForApply, setActiveRunForApply] = useState<RunViewV2 | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  const JOBS_PAGE_SIZE = 20;

  // Fetch initial profile & stats
  useEffect(() => {
    if (!profile) fetchProfile();
    const loadStats = () => {
      apiFetch('/api/stats')
        .then((r) => r.json())
        .then((d) => setExtraStats({ tailored: d.total_tailored || 0, interviews: d.total_interview || 0 }))
        .catch(() => {});
    };
    loadStats();
    const iv = setInterval(loadStats, 30000);
    return () => clearInterval(iv);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // TanStack Query: Fetch Jobs
  const {
    data: jobs = [],
    isLoading: isJobsLoading,
    refetch: refetchJobs,
  } = useQuery<JobViewV2[]>({
    queryKey: ['v2jobs', filters.remoteOnly, filters.minScore],
    queryFn: () =>
      listJobsV2({
        limit: 200,
        min_score: filters.minScore > 0 ? filters.minScore : undefined,
        remote_only: filters.remoteOnly || undefined,
      }),
    refetchInterval: 15000,
  });

  // TanStack Query: Fetch Runs
  const { data: runs = [], refetch: refetchRuns } = useQuery<RunViewV2[]>({
    queryKey: ['v2runs'],
    queryFn: () => listRunsV2({ limit: 30 }),
    refetchInterval: 8000,
  });

  // TanStack Query: ATS Score
  const { data: atsData } = useQuery({
    queryKey: ['recruiter-score-summary'],
    queryFn: async () => {
      const res = await apiFetch('/api/recruiter_score');
      if (!res.ok) return null;
      return res.json();
    },
    staleTime: 60000,
  });

  // SSE event stream subscription
  useEffect(() => {
    const unsub = subscribeToRunsV2(() => {
      queryClient.invalidateQueries({ queryKey: ['v2runs'] });
      queryClient.invalidateQueries({ queryKey: ['v2jobs'] });
    });
    return unsub;
  }, [queryClient]);

  // Filtered & Sorted Jobs
  const filteredJobs = useMemo(() => {
    let list = Array.isArray(jobs) ? [...jobs] : [];
    if (filters.searchQuery.trim()) {
      const q = filters.searchQuery.toLowerCase();
      list = list.filter(
        (j) =>
          j.title?.toLowerCase().includes(q) ||
          j.company?.toLowerCase().includes(q) ||
          j.location?.toLowerCase().includes(q) ||
          j.description?.toLowerCase().includes(q)
      );
    }
    list.sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0));
    return list;
  }, [jobs, filters.searchQuery]);

  // Paginated Jobs for 120 FPS buttery smooth scrolling
  const totalJobPages = Math.ceil(filteredJobs.length / JOBS_PAGE_SIZE) || 1;
  const paginatedJobs = useMemo(() => {
    const start = (jobPage - 1) * JOBS_PAGE_SIZE;
    return filteredJobs.slice(start, start + JOBS_PAGE_SIZE);
  }, [filteredJobs, jobPage]);

  // Keyboard shortcuts run only outside editable controls and active dialogs.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isTyping = target?.closest('input, textarea, select, [contenteditable="true"]');
      if (e.key === 'Escape') {
        setActiveDrawer('none');
        return;
      }
      if (isTyping) return;
      if (e.key === '/' || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k')) {
        if (activeDrawer !== 'none') return;
        e.preventDefault();
        document.getElementById('command-search')?.focus();
        return;
      }
      if (e.ctrlKey || e.metaKey || e.altKey || activeDrawer !== 'none') return;
      // Do not steal native Space/Enter activation from focused buttons or links.
      if (target?.closest('button, a, [role="button"]')) return;
      if (e.key === '1') setActiveTab('warfare');
      if (e.key === '2') setActiveTab('jobs');
      if (e.key === '3') setActiveTab('analytics');
      if (e.key === '4') setActiveTab('pipeline');
      if (e.key === '5') setActiveTab('skills');
      if (e.key.toLowerCase() === 'j' || e.key.toLowerCase() === 'k') {
        if (!paginatedJobs.length) return;
        e.preventDefault();
        const index = paginatedJobs.findIndex((job) => job.id === selectedJob?.id);
        const next = e.key.toLowerCase() === 'j'
          ? (index + 1) % paginatedJobs.length
          : (index <= 0 ? paginatedJobs.length - 1 : index - 1);
        setSelectedJob(paginatedJobs[next]);
      }
      if (selectedJob && (e.key === ' ' || e.key.toLowerCase() === 'a')) {
        e.preventDefault();
        setActiveDrawer(e.key === ' ' ? 'ats' : 'tailor');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [paginatedJobs, selectedJob, activeDrawer]);

  // Computed metrics
  const statVals = useMemo(() => {
    const scored = jobs.filter((j) => j.match_score != null);
    return {
      total: jobs.length,
      strong: jobs.filter((j) => (j.match_score ?? 0) >= 75).length,
      avg: scored.length ? Math.round(scored.reduce((a, j) => a + (j.match_score || 0), 0) / scored.length) : 0,
      remote: jobs.length ? Math.round((jobs.filter((j) => j.remote).length / jobs.length) * 100) : 0,
      tailored: extraStats.tailored,
      interviews: extraStats.interviews,
    };
  }, [jobs, extraStats]);

  // Autonomous Resume Upgrade Action
  const handleAutonomousUpgrade = async () => {
    setIsUpgradingResume(true);
    toast.loading('Running HackerRank AI audit & zero-hallucination fix...', { id: 'upgrade' });
    try {
      const res = await apiFetch('/api/resume/autonomous-upgrade', { method: 'POST' });
      if (!res.ok) throw new Error('Upgrade request failed');
      const data = await res.json();
      toast.success(
        `Audit Complete! Score: ${data.before_score}/120 -> ${data.after_score}/120 (+${data.delta} pts)`,
        { id: 'upgrade', duration: 6000 }
      );
      fetchRecruiterScore();
      queryClient.invalidateQueries({ queryKey: ['recruiter-score-summary'] });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error(`Upgrade failed: ${message}`, { id: 'upgrade' });
    } finally {
      setIsUpgradingResume(false);
    }
  };

  const handleRefreshAll = useCallback(() => {
    refetchJobs();
    refetchRuns();
    fetchRecruiterScore();
    toast.success('Refreshing job feeds and pipeline status...');
  }, [refetchJobs, refetchRuns, fetchRecruiterScore]);

  return (
    <div className="w-full h-full flex flex-col p-3 md:p-5 overflow-hidden relative gap-3.5">
      {/* ═══════════ HEADER BAR ═══════════ */}
      <HeaderBar
        name={profile?.name || 'Animesh Shukla'}
        jobCount={jobs.length}
        strongCount={statVals.strong}
        atsScore={atsData?.total}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onRefresh={handleRefreshAll}
        onOpenSettings={() => setActiveDrawer('setup')}
      />

      {/* ═══════════ LIGHTWEIGHT STATS TICKER ═══════════ */}
      <StatsStrip vals={statVals} />

      {/* ═══════════ TAB CONTENT AREA ═══════════ */}
      <div className="flex-1 min-h-0 overflow-hidden relative">
        {/* ── TAB 0: APEX WARFARE ENGINE ── */}
        {activeTab === 'warfare' && (
          <div className="h-full overflow-y-auto pr-1 custom-scrollbar">
            <Suspense fallback={<DrawerFallback />}>
              <ApexWarfareCenter />
            </Suspense>
          </div>
        )}

        {/* ── TAB 1: JOBS ── */}
        {activeTab === 'jobs' && (
          <div className="h-full flex flex-col gap-3 overflow-hidden">
            {/* Command & Filter Bar */}
            <CommandBar
              onSearchStarted={(id) => {
                setActiveRunId(id);
                refetchRuns();
              }}
              onFilterChange={setFilters}
              activeFilters={filters}
              onOpenSettings={() => setActiveDrawer('setup')}
            />

            {/* Sub-header with count and pagination */}
            <div className="flex items-center justify-between px-1 shrink-0 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-sm">Best Matched Roles</span>
                <span className="px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 font-mono font-bold text-xs">
                  {filteredJobs.length} available
                </span>
                {statVals.strong > 0 && (
                  <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold text-[11px]">
                    <TrendingUp size={11} /> {statVals.strong} strong fits
                  </span>
                )}
              </div>

              {/* Pagination controls */}
              {totalJobPages > 1 && (
                <div className="flex items-center gap-2 text-zinc-400">
                  <span>
                    Page <b className="text-white font-mono">{jobPage}</b> of {totalJobPages}
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setJobPage((p) => Math.max(1, p - 1))}
                      disabled={jobPage === 1}
                      className="p-1 rounded bg-white/[0.03] border border-white/[0.06] disabled:opacity-30 hover:bg-white/[0.06] text-zinc-300"
                    >
                      <ChevronLeft size={13} />
                    </button>
                    <button
                      onClick={() => setJobPage((p) => Math.min(totalJobPages, p + 1))}
                      disabled={jobPage === totalJobPages}
                      className="p-1 rounded bg-white/[0.03] border border-white/[0.06] disabled:opacity-30 hover:bg-white/[0.06] text-zinc-300"
                    >
                      <ChevronRight size={13} />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Jobs Feed List */}
            <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar min-h-0">
              <LiveIntelFeed
                jobs={paginatedJobs}
                isLoading={isJobsLoading}
                onSelectJob={(j) => {
                  setSelectedJob(j);
                  setActiveDrawer('detail');
                }}
                onOpenAtsBreakdown={(j) => {
                  setSelectedJob(j);
                  setActiveDrawer('ats');
                }}
                selectedJobId={selectedJob?.id}
              />
            </div>
          </div>
        )}

        {/* ── TAB 2: ATS & ANALYTICS ── */}
        {activeTab === 'analytics' && (
          <div className="h-full overflow-y-auto pr-1 custom-scrollbar space-y-4">
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
              {/* Left Column: Radial ATS Gauge + Categories */}
              <div className="xl:col-span-6 flex flex-col gap-4">
                <ATSOverviewCard
                  onUpgradeClick={handleAutonomousUpgrade}
                  isUpgrading={isUpgradingResume}
                />
                <FunnelPanel discovered={jobs.length} />
              </div>

              {/* Right Column: Detailed Rule Scorecard */}
              <div className="xl:col-span-6 flex flex-col gap-4">
                <div className="p-4 md:p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex flex-col gap-3">
                  <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                    <div className="flex items-center gap-2">
                      <Target size={16} className="text-emerald-400" />
                      <h3 className="text-base font-bold text-white">
                        HackerRank Rubric Impact Analysis
                      </h3>
                    </div>
                    <span className="text-xs text-zinc-500">Per-Rule Evidence</span>
                  </div>
                  <RecruiterScoreCard />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 3: PIPELINE & ENGINE ── */}
        {activeTab === 'pipeline' && (
          <div className="h-full overflow-y-auto pr-1 custom-scrollbar space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <div className="lg:col-span-8">
                <PipelineStatusPanel
                  runs={runs}
                  activeRunId={activeRunId}
                  onRefreshRuns={() => refetchRuns()}
                />
              </div>

              <div className="lg:col-span-4 space-y-4">
                <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] text-xs text-zinc-400 space-y-2.5">
                  <div className="flex items-center gap-2 text-zinc-200 font-semibold text-sm">
                    <Settings size={15} className="text-indigo-400" />
                    <span>Engine Specifications</span>
                  </div>
                  <div className="space-y-1.5 pt-2 border-t border-white/[0.04] text-[11px] font-mono">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Skills Directory:</span>
                      <span className="text-indigo-300">D:\skills-library</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Antigravity Path:</span>
                      <span className="text-indigo-300">~/.gemini/config/skills</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Active Port:</span>
                      <span className="text-emerald-400">http://127.0.0.1:8000</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Local Cache:</span>
                      <span className="text-zinc-300">data/hf_cache</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] text-xs text-zinc-500 space-y-2">
                  <div className="flex items-center gap-2 text-zinc-300 font-semibold">
                    <Shield size={14} className="text-emerald-400" /> Privacy & Automation Guard
                  </div>
                  <p className="leading-relaxed">
                    Zero applications submitted autonomously without your review. Resumes are tailored locally and verified against fabrication before final export.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 4: SKILLS & PLAYBOOKS ── */}
        {activeTab === 'skills' && (
          <Suspense fallback={<DrawerFallback />}>
            <SkillsLibraryPanel />
          </Suspense>
        )}
      </div>

      <LiveAgentConsole />

      {/* ──────────────────── DRAWERS ──────────────────── */}
      {activeDrawer !== 'none' && (
        <Suspense fallback={<DrawerFallback />}>
          {activeDrawer === 'detail' && (
            <JobDetailDrawer
              job={selectedJob}
              onClose={() => setActiveDrawer('none')}
              onOpenTailor={(j) => {
                setSelectedJob(j);
                setActiveDrawer('tailor');
              }}
              onOpenPrepareApply={(j, run) => {
                setSelectedJob(j);
                if (run) setActiveRunForApply(run);
                setActiveDrawer('prepare');
              }}
              onAuditStarted={(id) => {
                setActiveRunId(id);
                refetchRuns();
              }}
            />
          )}
          {activeDrawer === 'tailor' && (
            <TailorDrawer
              job={selectedJob}
              onClose={() => setActiveDrawer('none')}
              onProceedToApply={(j, run) => {
                setSelectedJob(j);
                if (run) setActiveRunForApply(run);
                setActiveDrawer('prepare');
              }}
            />
          )}
          {activeDrawer === 'prepare' && (
            <PrepareApplyDrawer
              job={selectedJob}
              run={activeRunForApply}
              onClose={() => setActiveDrawer('none')}
            />
          )}
          {activeDrawer === 'setup' && (
            <SettingsDrawer onClose={() => setActiveDrawer('none')} onStatusChange={() => {}} />
          )}
          {activeDrawer === 'ats' && selectedJob && (
            <AtsBreakdownModal
              job={selectedJob}
              onClose={() => setActiveDrawer('none')}
              onOpenTailor={(j) => {
                setSelectedJob(j);
                setActiveDrawer('tailor');
              }}
            />
          )}
        </Suspense>
      )}
    </div>
  );
}
