/* eslint-disable @typescript-eslint/no-explicit-any */
import { Job } from '../types';
import React, { useState, useEffect } from 'react';
import { Search, Globe, RefreshCw, Star, AlertTriangle, TrendingUp, CheckCircle, ChevronDown, ChevronUp, ExternalLink, BookmarkPlus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function FindJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [urlInput, setUrlInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Apify Scraper Inputs
  const [apifyQuery, setApifyQuery] = useState('');
  const [apifyLoc] = useState('');
  const [apifyLimit] = useState(10);
  const [apifyRunning, setApifyRunning] = useState(false);

  // States
  const [loading, setLoading] = useState(false);
  const [expandedJobId, setExpandedJobId] = useState<number | null>(null);
  const [insights, setInsights] = useState<any>({});
  const [insightsLoading, setInsightsLoading] = useState<number | null>(null);
  const [scoringAll, setScoringAll] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  async function fetchJobs() {
    setLoading(true);
    try {
      const r = await fetch('/api/jobs');
      const data = await r.json();
      setJobs(data);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchJobs();
  }, []);

  const handleScrapeUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    
    setLoading(true);
    setMessage({ text: 'Extracting job details...', type: 'info' });
    try {
      const r = await fetch('/api/jobs/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlInput }),
      });
      const data = await r.json();
      if (r.ok) {
        setMessage({ text: `Successfully scraped: ${data.job.title}`, type: 'success' });
        setUrlInput('');
        fetchJobs();
      } else {
        setMessage({ text: data.detail || 'Failed to scrape job.', type: 'error' });
      }
    } catch (err: any) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleApifyScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apifyQuery.trim()) return;

    setApifyRunning(true);
    setMessage({ text: 'Triggering background job miner...', type: 'info' });
    try {
      const r = await fetch('/api/jobs/apify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: apifyQuery,
          location: apifyLoc || 'Remote',
          limit: apifyLimit
        })
      });
      if (r.ok) {
        setMessage({ text: 'Miner started. Check back later.', type: 'success' });
        setApifyQuery('');
      } else {
        const data = await r.json();
        setMessage({ text: data.detail || 'Failed to trigger miner.', type: 'error' });
      }
    } catch (err: any) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' });
    } finally {
      setApifyRunning(false);
    }
  };

  const handleCalculateScore = async (id: number) => {
    try {
      const r = await fetch(`/api/jobs/${id}/score`, { method: 'POST' });
      const data = await r.json();
      if (r.ok) {
        setJobs(prev => prev.map(j => j.id === id ? { ...j, match_score: data.score, match_reason: data.reason } : j));
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleScoreAll = async () => {
    setScoringAll(true);
    setMessage({ text: 'Batch scoring started...', type: 'info' });
    try {
      const r = await fetch('/api/jobs/score-all', { method: 'POST' });
      if (r.ok) {
        setMessage({ text: 'Batch scoring in progress.', type: 'success' });
        setTimeout(fetchJobs, 5000); 
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setScoringAll(false);
    }
  };

  const handleExpandJob = async (job: Job) => {
    if (expandedJobId === job.id) {
      setExpandedJobId(null);
      return;
    }

    setExpandedJobId(job.id);
    if (!insights[job.id]) {
      setInsightsLoading(job.id);
      try {
        const r = await fetch(`/api/jobs/${job.id}/insights`);
        const data = await r.json();
        setInsights((prev: Record<number, unknown>) => ({ ...prev, [job.id]: data }));
      } catch (e: any) {
        console.error(e);
      } finally {
        setInsightsLoading(null);
      }
    }
  };

  const handleSaveToApply = async (jobId: number) => {
    try {
      const r = await fetch(`/api/applications/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Saved' }),
      });
      if (r.ok) {
        setMessage({ text: 'Added to tracker!', type: 'success' });
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const filteredJobs = jobs.filter(job => {
    const term = searchQuery.toLowerCase();
    return (
      (job.title || '').toLowerCase().includes(term) ||
      (job.company || '').toLowerCase().includes(term)
    );
  });

  const getMatchTier = (score: number) => {
    if (!score) return null;
    if (score >= 8) return 'strong';
    if (score >= 6) return 'moderate';
    return 'weak';
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16 pt-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Inbox</h1>
          <p className="text-sm text-muted mt-1">Review and filter your incoming job matches.</p>
        </div>
        
        <div className="flex items-center gap-2">
          <button onClick={handleScoreAll} disabled={scoringAll} className="btn-minimal flex items-center gap-2">
            <RefreshCw size={14} className={scoringAll ? 'animate-spin' : ''} />
            Score All
          </button>
          <button onClick={fetchJobs} disabled={loading} className="btn-minimal">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {message.text && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} 
          className="bg-white/5 border border-white/10 p-3 rounded-lg text-sm flex items-center gap-2">
          {message.type === 'error' ? <AlertTriangle size={16} className="text-red-400" /> : <CheckCircle size={16} className="text-emerald-400" />}
          <span className="text-gray-300">{message.text}</span>
        </motion.div>
      )}

      {/* Import Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <form onSubmit={handleScrapeUrl} className="flex gap-2">
          <div className="relative flex-1">
            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
            <input type="url" required value={urlInput} onChange={(e) => setUrlInput(e.target.value)}
              className="minimal-input w-full pl-9" placeholder="Paste URL (Greenhouse, Lever, etc)" />
          </div>
          <button type="submit" disabled={loading} className="btn-primary px-4 py-2 text-sm rounded-md shrink-0">
            Import
          </button>
        </form>

        <form onSubmit={handleApifyScrape} className="flex gap-2">
          <div className="relative flex-1">
            <TrendingUp className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
            <input type="text" required value={apifyQuery} onChange={(e) => setApifyQuery(e.target.value)}
              className="minimal-input w-full pl-9" placeholder="Automated Search (e.g. Software Engineer)" />
          </div>
          <button type="submit" disabled={apifyRunning} className="btn-minimal shrink-0">
            {apifyRunning ? "Scanning..." : "Start Scan"}
          </button>
        </form>
      </div>

      {/* Main List */}
      <div className="surface-panel">
        <div className="p-3 border-b border-white/10 flex items-center gap-3">
          <Search className="text-gray-500" size={16} />
          <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent border-none focus:outline-none text-sm text-white w-full" 
            placeholder="Filter by title or company..." />
        </div>

        <div className="flex flex-col">
          {filteredJobs.length === 0 ? (
            <div className="p-8 text-center text-sm text-gray-500">
              No jobs found in your inbox.
            </div>
          ) : (
            filteredJobs.map((job) => {
              const isExpanded = expandedJobId === job.id;
              const jobInsights = insights[job.id];
              const tier = getMatchTier(job.match_score);
              
              return (
                <div key={job.id} className="flex flex-col">
                  {/* Dense Row */}
                  <div className="list-card gap-4" onClick={() => handleExpandJob(job)}>
                    <div className="w-4 flex justify-center shrink-0">
                      {tier ? (
                        <span className={`match-dot ${tier}`} title={`Score: ${job.match_score}/10`} />
                      ) : (
                        <button onClick={(e) => { e.stopPropagation(); handleCalculateScore(job.id); }} className="text-gray-600 hover:text-white">
                          <Star size={14} />
                        </button>
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0 flex flex-col md:flex-row md:items-center gap-1 md:gap-4">
                      <h3 className="text-sm font-medium text-gray-100 truncate md:w-5/12">{job.title}</h3>
                      <p className="text-sm text-gray-400 truncate md:w-3/12">{job.company}</p>
                      <p className="text-xs text-gray-500 truncate md:w-3/12">{job.location}</p>
                    </div>

                    <div className="shrink-0 text-gray-500">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {/* Expanded Content */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden bg-[#18181b] border-b border-white/5"
                      >
                        <div className="p-6 space-y-6">
                          <div className="flex justify-between items-start">
                            <div>
                              <h4 className="font-medium text-white mb-1">{job.company} — {job.title}</h4>
                              <p className="text-sm text-muted mb-4">Added {new Date(job.created_at).toLocaleDateString()}</p>
                              
                              {job.match_reason && (
                                <p className="text-sm text-gray-300 italic border-l-2 border-indigo-500/50 pl-3 py-1 mb-4">
                                  {job.match_reason}
                                </p>
                              )}
                            </div>
                            
                            <div className="flex gap-2">
                              <a href={job.url} target="_blank" rel="noreferrer" className="btn-minimal flex items-center gap-1">
                                <ExternalLink size={14} /> View
                              </a>
                              <button onClick={() => handleSaveToApply(job.id)} className="btn-primary flex items-center gap-1 px-3 py-1.5 text-sm rounded-md">
                                <BookmarkPlus size={14} /> Save
                              </button>
                            </div>
                          </div>

                          {insightsLoading === job.id ? (
                            <div className="text-sm text-gray-400 flex items-center gap-2">
                              <RefreshCw size={14} className="animate-spin" /> Loading AI Insights...
                            </div>
                          ) : jobInsights ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                              {/* Strengths */}
                              <div className="space-y-2">
                                <h5 className="font-medium text-emerald-400">Match Strengths</h5>
                                <ul className="list-disc pl-4 text-gray-300 space-y-1">
                                  {jobInsights.fit_analysis?.matched_skills?.slice(0, 3).map((s: string) => <li key={s}>{s}</li>) || <li className="text-gray-500">None detected</li>}
                                </ul>
                              </div>
                              {/* Gaps */}
                              <div className="space-y-2">
                                <h5 className="font-medium text-amber-400">Skill Gaps</h5>
                                <ul className="list-disc pl-4 text-gray-300 space-y-1">
                                  {jobInsights.fit_analysis?.missing_skills?.slice(0, 3).map((s: string) => <li key={s}>{s}</li>) || <li className="text-gray-500">None detected</li>}
                                </ul>
                              </div>
                              {/* Red Flags */}
                              {Object.keys(jobInsights.red_flags || {}).length > 0 && (
                                <div className="space-y-2 md:col-span-2 pt-2 border-t border-white/5">
                                  <h5 className="font-medium text-rose-400 flex items-center gap-1"><AlertTriangle size={14}/> Red Flags</h5>
                                  <div className="flex flex-wrap gap-2">
                                    {Object.entries(jobInsights.red_flags).map(([cat]) => (
                                      <span key={cat} className="px-2 py-0.5 bg-rose-500/10 text-rose-300 rounded text-xs capitalize border border-rose-500/20">{cat.replace('_', ' ')}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ) : null}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
