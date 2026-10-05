import React, { useState } from 'react';
import { Search, Sparkles, Filter, X, Play, Loader2, User } from 'lucide-react';
import { triggerSearchV2, type SearchIntentV2 } from '../api/v2Client';
import toast from 'react-hot-toast';

interface CommandBarProps {
  onSearchStarted: (runId: string) => void;
  onFilterChange: (filters: { remoteOnly: boolean; minScore: number; searchQuery: string }) => void;
  activeFilters: { remoteOnly: boolean; minScore: number; searchQuery: string };
  onOpenSettings: () => void;
}

export default function CommandBar({ onSearchStarted, onFilterChange, activeFilters, onOpenSettings }: CommandBarProps) {
  const [query, setQuery] = useState(activeFilters.searchQuery);
  const [isExecuting, setIsExecuting] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  
  // Natural language parsing helpers
  const parseAndExecute = async () => {
    if (!query.trim()) {
      toast.error('Enter a job search query or title');
      return;
    }

    setIsExecuting(true);
    try {
      // Simple natural language extraction
      const lower = query.toLowerCase();
      const remoteOnly = activeFilters.remoteOnly || lower.includes('remote');
      let location: string | undefined = undefined;
      
      if (lower.includes('in ')) {
        const parts = query.split(/\bin\b/i);
        if (parts.length > 1) {
          location = parts[1].split(' ')[0];
        }
      }

      const intent: SearchIntentV2 = {
        query: query.replace(/remote/ig, '').trim() || query,
        location,
        remote_only: remoteOnly,
        sources: ['remoteok', 'arbeitnow', 'hackernews', 'linkedin'],
        auto_apply: false
      };

      const run = await triggerSearchV2(intent);
      toast.success(`Search run started: ${run.run_id}`);
      onSearchStarted(run.run_id);
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : String(e);
      toast.error(`Search failed to start: ${err}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      parseAndExecute();
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto mb-6">
      <div className="relative w-full">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-indigo-400" />
        </div>
        
        <input
          id="command-search"
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            onFilterChange({ ...activeFilters, searchQuery: e.target.value });
          }}
          onKeyDown={handleKeyDown}
          placeholder="Search jobs, roles, companies... e.g. 'Senior AI Engineer remote $180k'"
          className="w-full h-14 pl-12 pr-36 bg-[#0c0c0e]/90 border border-indigo-500/30 rounded-2xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 shadow-[0_0_30px_-5px_rgba(99,102,241,0.25)] backdrop-blur-xl transition-all font-medium text-sm md:text-base"
        />

        <div className="absolute inset-y-0 right-2 flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-xl border text-xs font-medium flex items-center gap-1.5 transition-colors ${
              showFilters || activeFilters.remoteOnly || activeFilters.minScore > 0
                ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
                : 'bg-white/5 border-white/10 text-zinc-400 hover:text-white'
            }`}
            title="Toggle Filters"
          >
            <Filter size={14} />
            <span className="hidden sm:inline">Filters</span>
          </button>

          <button
            onClick={onOpenSettings}
            className="p-2 rounded-xl border border-white/10 bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all flex items-center gap-1.5 active:scale-95"
            title="Profile & Settings"
          >
            <User size={14} />
            <span className="hidden sm:inline text-xs font-medium">Profile</span>
          </button>

          <button
            onClick={parseAndExecute}
            disabled={isExecuting}
            className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 disabled:opacity-50 text-white text-xs md:text-sm font-semibold rounded-xl shadow-lg shadow-indigo-500/20 flex items-center gap-2 transition-all active:scale-95"
          >
            {isExecuting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Play size={14} className="fill-white" />
                <span>Execute</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Filter Chips Bar */}
      {(showFilters || activeFilters.remoteOnly || activeFilters.minScore > 0) && (
        <div className="mt-3 p-3.5 rounded-xl bg-[#0c0c0e]/80 border border-white/10 flex flex-wrap items-center gap-3 backdrop-blur-md animate-in fade-in slide-in-from-top-2 duration-200">
          <span className="text-xs font-semibold text-zinc-400 flex items-center gap-1.5">
            <Sparkles size={13} className="text-indigo-400" />
            Active Filters:
          </span>

          {/* Remote Only Chip */}
          <button
            onClick={() => onFilterChange({ ...activeFilters, remoteOnly: !activeFilters.remoteOnly })}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-all flex items-center gap-1.5 ${
              activeFilters.remoteOnly
                ? 'bg-indigo-500/20 border-indigo-500 text-indigo-300'
                : 'bg-white/5 border-white/10 text-zinc-400 hover:border-white/20'
            }`}
          >
            <span>Remote Only</span>
            {activeFilters.remoteOnly && <X size={12} />}
          </button>

          {/* Min Score Chip */}
          <div className="flex items-center gap-1.5 bg-white/5 border border-white/10 px-3 py-1 rounded-full text-xs">
            <span className="text-zinc-400">Min Fit Score:</span>
            <select
              value={activeFilters.minScore}
              onChange={(e) => onFilterChange({ ...activeFilters, minScore: Number(e.target.value) })}
              className="bg-transparent text-indigo-300 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="0" className="bg-[#0c0c0e] text-white">All Scores (0+)</option>
              <option value="60" className="bg-[#0c0c0e] text-white">Good Fit (60+)</option>
              <option value="75" className="bg-[#0c0c0e] text-white">Strong Fit (75+)</option>
              <option value="85" className="bg-[#0c0c0e] text-white">Top Match (85+)</option>
            </select>
          </div>

          {(activeFilters.remoteOnly || activeFilters.minScore > 0) && (
            <button
              onClick={() => onFilterChange({ ...activeFilters, remoteOnly: false, minScore: 0 })}
              className="text-xs text-zinc-500 hover:text-red-400 underline ml-auto transition-colors"
            >
              Reset filters
            </button>
          )}
        </div>
      )}
    </div>
  );
}
