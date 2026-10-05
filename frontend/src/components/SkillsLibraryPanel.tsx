import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sparkles,
  Search,
  RefreshCw,
  BookOpen,
  Code2,
  ShieldAlert,
  Cpu,
  Terminal,
  Briefcase,
  Layers,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiFetch } from '../utils/api';

export interface SkillItem {
  id: string;
  name: string;
  description: string;
  category: string;
  path: string;
  has_scripts: boolean;
  has_references: boolean;
}

export interface SkillCatalogResponse {
  skills: SkillItem[];
  total: number;
  filtered_count: number;
  categories: Record<string, number>;
}

export interface SkillDetailResponse {
  id: string;
  name: string;
  description: string;
  category: string;
  content: string;
  path: string;
}

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  'Career & Resume': Briefcase,
  'Scraping & Automation': Terminal,
  'Code Quality & Testing': CheckCircle2,
  'Security & Audit': ShieldAlert,
  'AI & Reasoning': Cpu,
  'Cloud & DevOps': Layers,
  'Media & Creative': Sparkles,
  'Core Engineering': Code2,
};

const CATEGORY_COLORS: Record<string, { badge: string; border: string; glow: string }> = {
  'Career & Resume': { badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30', border: 'hover:border-emerald-500/40', glow: 'rgba(52,211,153,0.15)' },
  'Scraping & Automation': { badge: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30', border: 'hover:border-cyan-500/40', glow: 'rgba(6,182,212,0.15)' },
  'Code Quality & Testing': { badge: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30', border: 'hover:border-indigo-500/40', glow: 'rgba(99,102,241,0.15)' },
  'Security & Audit': { badge: 'bg-rose-500/15 text-rose-300 border-rose-500/30', border: 'hover:border-rose-500/40', glow: 'rgba(244,63,94,0.15)' },
  'AI & Reasoning': { badge: 'bg-purple-500/15 text-purple-300 border-purple-500/30', border: 'hover:border-purple-500/40', glow: 'rgba(168,85,247,0.15)' },
  'Cloud & DevOps': { badge: 'bg-sky-500/15 text-sky-300 border-sky-500/30', border: 'hover:border-sky-500/40', glow: 'rgba(56,189,248,0.15)' },
  'Media & Creative': { badge: 'bg-amber-500/15 text-amber-300 border-amber-500/30', border: 'hover:border-amber-500/40', glow: 'rgba(245,158,11,0.15)' },
  'Core Engineering': { badge: 'bg-zinc-500/15 text-zinc-300 border-zinc-500/30', border: 'hover:border-zinc-500/40', glow: 'rgba(113,113,122,0.15)' },
};

const ITEMS_PER_PAGE = 24;

export default function SkillsLibraryPanel() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [page, setPage] = useState(1);
  const [activeSkillId, setActiveSkillId] = useState<string | null>(null);

  // Query catalog
  const { data, isLoading } = useQuery<SkillCatalogResponse>({
    queryKey: ['skills-catalog'],
    queryFn: async () => {
      const res = await apiFetch('/api/skills');
      if (!res.ok) throw new Error('Failed to load skills catalog');
      return res.json();
    },
    staleTime: 60000,
  });

  // Query single skill detail
  const { data: activeSkillDetail, isLoading: isLoadingDetail } = useQuery<SkillDetailResponse>({
    queryKey: ['skill-detail', activeSkillId],
    queryFn: async () => {
      if (!activeSkillId) throw new Error('No skill selected');
      const res = await apiFetch(`/api/skills/${activeSkillId}`);
      if (!res.ok) throw new Error('Failed to fetch skill details');
      return res.json();
    },
    enabled: Boolean(activeSkillId),
  });

  // Refresh mutation
  const refreshMutation = useMutation({
    mutationFn: async () => {
      const res = await apiFetch('/api/skills/refresh', { method: 'POST' });
      return res.json();
    },
    onSuccess: (result) => {
      toast.success(`Skills library rescanned: ${result.total} skills ready!`);
      queryClient.invalidateQueries({ queryKey: ['skills-catalog'] });
    },
    onError: () => {
      toast.error('Failed to refresh skills library.');
    },
  });

  // Filter skills
  const filteredSkills = useMemo(() => {
    if (!data?.skills) return [];
    let list = data.skills;

    if (selectedCategory !== 'All') {
      list = list.filter((s) => s.category.toLowerCase() === selectedCategory.toLowerCase());
    }

    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.id.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q)
      );
    }

    return list;
  }, [data?.skills, selectedCategory, search]);

  // Pagination
  const totalPages = Math.ceil(filteredSkills.length / ITEMS_PER_PAGE) || 1;
  const paginatedSkills = useMemo(() => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    return filteredSkills.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredSkills, page]);

  const handleCategoryClick = (cat: string) => {
    setSelectedCategory(cat);
    setPage(1);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const categories = useMemo(() => {
    if (!data?.categories) return [];
    return Object.entries(data.categories).sort((a, b) => b[1] - a[1]);
  }, [data]);

  return (
    <div className="h-full flex flex-col gap-4 overflow-hidden relative">
      {/* ── Top Header Banner ── */}
      <div className="p-4 md:p-5 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-zinc-900/40 border border-white/[0.08] shadow-[0_4px_24px_rgba(0,0,0,0.3)] shrink-0">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Sparkles size={16} />
              </div>
              <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Antigravity Agent Skills Library
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono font-bold">
                  {data?.total ?? '1,642'} Installed
                </span>
              </h2>
            </div>
            <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
              Connected directly to <code className="text-indigo-300 font-mono text-[11px] bg-white/[0.04] px-1.5 py-0.5 rounded">D:\skills-library</code> & <code className="text-indigo-300 font-mono text-[11px] bg-white/[0.04] px-1.5 py-0.5 rounded">~/.gemini/config/skills</code>. Any subagent or planner can progressively invoke these playbooks on demand.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={() => refreshMutation.mutate()}
              disabled={refreshMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-zinc-300 hover:text-white text-xs font-medium transition-colors disabled:opacity-50"
              title="Rescan D:\skills-library"
            >
              <RefreshCw size={13} className={refreshMutation.isPending ? 'animate-spin' : ''} />
              <span>Rescan Disk</span>
            </button>
          </div>
        </div>

        {/* ── Search & Filter Row ── */}
        <div className="mt-4 flex flex-col md:flex-row items-stretch md:items-center gap-3">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              value={search}
              onChange={handleSearchChange}
              placeholder="Search 1,600+ skills by title, capability, keyword (e.g. stealth, resume, tdd, docker)..."
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-black/40 border border-white/[0.08] text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
              >
                <X size={13} />
              </button>
            )}
          </div>
        </div>

        {/* ── Category Pills ── */}
        <div className="mt-3 flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar">
          <button
            onClick={() => handleCategoryClick('All')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors shrink-0 flex items-center gap-1.5 ${
              selectedCategory === 'All'
                ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20'
                : 'bg-white/[0.03] text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.06] border border-white/[0.04]'
            }`}
          >
            <BookOpen size={12} />
            All ({data?.total ?? 0})
          </button>
          {categories.map(([cat, count]) => {
            const Icon = CATEGORY_ICONS[cat] || Code2;
            const active = selectedCategory.toLowerCase() === cat.toLowerCase();
            return (
              <button
                key={cat}
                onClick={() => handleCategoryClick(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors shrink-0 flex items-center gap-1.5 ${
                  active
                    ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20'
                    : 'bg-white/[0.03] text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.06] border border-white/[0.04]'
                }`}
              >
                <Icon size={12} />
                {cat} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Skills Grid ── */}
      <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar min-h-0">
        {isLoading ? (
          <div className="w-full py-20 flex flex-col items-center justify-center gap-3 text-zinc-500">
            <RefreshCw size={24} className="animate-spin text-indigo-400" />
            <p className="text-sm">Indexing 1,600+ Antigravity skills from disk...</p>
          </div>
        ) : filteredSkills.length === 0 ? (
          <div className="w-full py-20 px-4 text-center rounded-2xl bg-white/[0.01] border border-white/[0.04] flex flex-col items-center justify-center">
            <BookOpen size={32} className="text-zinc-600 mb-2" />
            <h3 className="text-base font-bold text-white">No skills match your search</h3>
            <p className="text-xs text-zinc-500 max-w-sm mt-1">
              Try searching with broader terms or choose "All" categories.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {paginatedSkills.map((skill) => {
              const Icon = CATEGORY_ICONS[skill.category] || Code2;
              const colorInfo = CATEGORY_COLORS[skill.category] || CATEGORY_COLORS['Core Engineering'];

              return (
                <div
                  key={skill.id}
                  onClick={() => setActiveSkillId(skill.id)}
                  className={`p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] ${colorInfo.border} hover:bg-white/[0.035] transition-all cursor-pointer group flex flex-col justify-between`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className="w-7 h-7 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-zinc-400 group-hover:text-indigo-300 transition-colors shrink-0">
                          <Icon size={14} />
                        </div>
                        <h4 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors truncate">
                          {skill.name}
                        </h4>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full border text-[10px] font-medium shrink-0 ${colorInfo.badge}`}>
                        {skill.category}
                      </span>
                    </div>

                    <p className="mt-2 text-xs text-zinc-400 line-clamp-2 leading-relaxed opacity-90 group-hover:opacity-100">
                      {skill.description}
                    </p>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-white/[0.04] flex items-center justify-between text-[11px] text-zinc-500">
                    <span className="font-mono text-[10px] text-zinc-600 truncate max-w-[180px]">
                      {skill.id}
                    </span>
                    <span className="text-indigo-400 flex items-center gap-1 font-medium group-hover:underline">
                      View Playbook <ChevronRight size={12} />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Pagination Bar ── */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2 pt-2 border-t border-white/[0.04] shrink-0 text-xs text-zinc-500">
          <div>
            Showing {(page - 1) * ITEMS_PER_PAGE + 1}–{Math.min(page * ITEMS_PER_PAGE, filteredSkills.length)} of {filteredSkills.length} skills
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] disabled:opacity-30 hover:bg-white/[0.06] text-zinc-300 transition-colors"
            >
              <ChevronLeft size={14} />
            </button>
            <span className="font-mono text-zinc-300">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] disabled:opacity-30 hover:bg-white/[0.06] text-zinc-300 transition-colors"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}

      {/* ── Skill Detail Slide-Over Drawer ── */}
      {activeSkillId && (
        <div
          className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity"
          onClick={() => setActiveSkillId(null)}
        >
          <div
            className="w-full max-w-2xl h-full bg-[#0a0a0e] border-l border-white/[0.08] shadow-2xl flex flex-col p-6 overflow-hidden relative z-10"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-4 pb-4 border-b border-white/[0.08] shrink-0">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-xs font-mono font-medium">
                    {activeSkillDetail?.category || 'Skill'}
                  </span>
                  <span className="text-zinc-500 text-xs font-mono">
                    {activeSkillDetail?.id}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mt-1">
                  {activeSkillDetail?.name || activeSkillId}
                </h3>
              </div>
              <button
                onClick={() => setActiveSkillId(null)}
                className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-zinc-400 hover:text-white transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto custom-scrollbar my-4 pr-1 text-sm text-zinc-300 space-y-4">
              {isLoadingDetail ? (
                <div className="py-20 flex flex-col items-center justify-center gap-3 text-zinc-500">
                  <RefreshCw size={24} className="animate-spin text-indigo-400" />
                  <p>Loading skill markdown documentation...</p>
                </div>
              ) : activeSkillDetail?.content ? (
                <div className="bg-black/30 p-4 rounded-xl border border-white/[0.04] font-mono text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">
                  {activeSkillDetail.content}
                </div>
              ) : (
                <p className="text-zinc-500">No documentation content available.</p>
              )}
            </div>

            {/* Footer */}
            <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between text-xs text-zinc-500 shrink-0">
              <span className="font-mono text-[11px] truncate max-w-sm">
                Path: {activeSkillDetail?.path}
              </span>
              <button
                onClick={() => setActiveSkillId(null)}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors"
              >
                Close Playbook
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
