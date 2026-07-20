import React, { useState, useEffect, useMemo } from 'react';
import { Sparkles, Terminal, Filter, RefreshCw } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { listJobsV2, listRunsV2, subscribeToRunsV2, type JobViewV2, type RunViewV2 } from '../api/v2Client';
import CommandBar from '../components/CommandBar';
import LiveIntelFeed from '../components/LiveIntelFeed';
import PipelineStatusPanel from '../components/PipelineStatusPanel';
import JobDetailDrawer from '../components/JobDetailDrawer';
import TailorDrawer from '../components/TailorDrawer';
import PrepareApplyDrawer from '../components/PrepareApplyDrawer';
import SettingsDrawer from '../components/SettingsDrawer';

export default function CommandCenter() {
  const queryClient = useQueryClient();

  // Filter & UI State
  const [filters, setFilters] = useState({
    remoteOnly: false,
    minScore: 0,
    searchQuery: ''
  });
  
  const [selectedJob, setSelectedJob] = useState<JobViewV2 | null>(null);
  const [activeDrawer, setActiveDrawer] = useState<'none' | 'detail' | 'tailor' | 'prepare' | 'setup'>('none');
  const [activeRunForApply, setActiveRunForApply] = useState<RunViewV2 | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  // TanStack Query: Fetch Jobs
  const {
    data: jobs = [],
    isLoading: isJobsLoading,
    refetch: refetchJobs
  } = useQuery<JobViewV2[]>({
    queryKey: ['v2jobs', filters.remoteOnly, filters.minScore],
    queryFn: () => listJobsV2({
      limit: 100,
      min_score: filters.minScore > 0 ? filters.minScore : undefined,
      remote_only: filters.remoteOnly ? true : undefined
    }),
    refetchInterval: 10000, // Background poll fallback
  });

  // TanStack Query: Fetch Runs
  const {
    data: runs = [],
    refetch: refetchRuns
  } = useQuery<RunViewV2[]>({
    queryKey: ['v2runs'],
    queryFn: () => listRunsV2({ limit: 30 }),
    refetchInterval: 5000,
  });

  // Subscribe to real-time SSE progress events
  useEffect(() => {
    const unsubscribe = subscribeToRunsV2(() => {
      // Refresh jobs & runs when SSE messages arrive
      queryClient.invalidateQueries({ queryKey: ['v2runs'] });
      queryClient.invalidateQueries({ queryKey: ['v2jobs'] });
    });

    return () => unsubscribe();
  }, [queryClient]);

  // Client-side text filtering over fetched jobs
  const filteredJobs = useMemo(() => {
    if (!filters.searchQuery.trim()) return jobs;
    const q = filters.searchQuery.toLowerCase();
    return jobs.filter((job) => {
      const matchTitle = job.title?.toLowerCase().includes(q);
      const matchCompany = job.company?.toLowerCase().includes(q);
      const matchLoc = job.location?.toLowerCase().includes(q);
      const matchDesc = job.description?.toLowerCase().includes(q);
      return matchTitle || matchCompany || matchLoc || matchDesc;
    });
  }, [jobs, filters.searchQuery]);

  // Drawer handlers
  const handleSelectJob = (job: JobViewV2) => {
    setSelectedJob(job);
    setActiveDrawer('detail');
  };

  const handleOpenTailor = (job: JobViewV2) => {
    setSelectedJob(job);
    setActiveDrawer('tailor');
  };

  const handleOpenPrepareApply = (job: JobViewV2, run?: RunViewV2) => {
    setSelectedJob(job);
    if (run) setActiveRunForApply(run);
    setActiveDrawer('prepare');
  };

  const handleCloseDrawer = () => {
    setActiveDrawer('none');
  };

  const handleSearchStarted = (runId: string) => {
    setActiveRunId(runId);
    refetchRuns();
  };

  const handleAuditStarted = (runId: string) => {
    setActiveRunId(runId);
    refetchRuns();
  };

  return (
    <div className="w-full h-full flex flex-col p-4 md:p-6 overflow-hidden relative">
      
      {/* Header Bar */}
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-[0_0_20px_-5px_rgba(99,102,241,0.3)]">
            <Sparkles size={20} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              Command Center
            </h1>
            <p className="text-xs text-zinc-400">Unified local-first AI job intelligence & review-first execution engine</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              refetchJobs();
              refetchRuns();
            }}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-400 hover:text-white text-xs flex items-center gap-1.5 transition-colors"
            title="Refresh Intelligence"
          >
            <RefreshCw size={14} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <div className="px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-mono font-semibold text-emerald-400 flex items-center gap-2 shadow-[0_0_15px_-3px_rgba(52,211,153,0.2)]">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            System Online
          </div>
        </div>
      </div>
      
      {/* Central Command Bar */}
      <CommandBar
        onSearchStarted={handleSearchStarted}
        onFilterChange={setFilters}
        activeFilters={filters}
        onOpenSettings={() => setActiveDrawer('setup')}
      />
      
      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0 overflow-hidden">
        
        {/* Left Column: Live Intel Feed */}
        <div className="lg:col-span-8 flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2 min-h-0">
          <div className="flex items-center justify-between shrink-0 px-1">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300">
                Live Intel Feed
              </h2>
              <span className="px-2 py-0.5 rounded-full bg-white/10 text-zinc-300 text-xs font-mono font-bold">
                {filteredJobs.length}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <Filter size={13} />
              <span>Real-time DB Sync</span>
            </div>
          </div>
          
          <LiveIntelFeed
            jobs={filteredJobs}
            isLoading={isJobsLoading}
            onSelectJob={handleSelectJob}
            selectedJobId={selectedJob?.id}
          />
        </div>
        
        {/* Right Column: Pipeline Status & Operations */}
        <div className="lg:col-span-4 flex flex-col gap-6 overflow-y-auto custom-scrollbar min-h-0">
          <PipelineStatusPanel
            runs={runs}
            activeRunId={activeRunId}
            onRefreshRuns={() => refetchRuns()}
          />

          {/* Quick System Diagnostics Info Card */}
          <div className="p-4 rounded-2xl bg-white/[0.015] border border-white/[0.05] text-xs text-zinc-400 space-y-2">
            <div className="flex items-center gap-2 text-zinc-300 font-semibold">
              <Terminal size={14} className="text-indigo-400" />
              <span>Capability Honesty Assurance</span>
            </div>
            <p className="leading-relaxed opacity-90">
              All active job searches, capabilities audits, and tailored resume generations run via local-first background workers. No action is ever submitted without explicit manual confirmation (`STAGED_READY_FOR_USER_REVIEW`).
            </p>
          </div>
        </div>
      </div>

      {/* Slide-Over Drawers */}
      {activeDrawer === 'detail' && (
        <JobDetailDrawer
          job={selectedJob}
          onClose={handleCloseDrawer}
          onOpenTailor={handleOpenTailor}
          onOpenPrepareApply={(job, run) => handleOpenPrepareApply(job, run)}
          onAuditStarted={handleAuditStarted}
        />
      )}

      {activeDrawer === 'tailor' && (
        <TailorDrawer
          job={selectedJob}
          onClose={handleCloseDrawer}
          onProceedToApply={(job, run) => handleOpenPrepareApply(job, run)}
        />
      )}

      {activeDrawer === 'prepare' && (
        <PrepareApplyDrawer
          job={selectedJob}
          run={activeRunForApply}
          onClose={handleCloseDrawer}
        />
      )}

      {activeDrawer === 'setup' && (
        <SettingsDrawer
          onClose={handleCloseDrawer}
          onStatusChange={() => {}}
        />
      )}
    </div>
  );
}
