/* eslint-disable @typescript-eslint/no-explicit-any */
import { Application } from '../types';
import React, { useState, useEffect } from 'react';
import { BarChart3, Clock, AlertTriangle, RefreshCw, MessageSquare, Save, X } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Tracker() {
  const [apps, setApps] = useState<Application[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  // Modal states
  const [selectedApp, setSelectedApp] = useState<any>(null);
  const [notesInput, setNotesInput] = useState('');
  const [statusSelect, setStatusSelect] = useState('');
  
  // Follow up draft states
  const [followupDraft, setFollowupDraft] = useState<any>(null);
  const [generatingFollowup, setGeneratingFollowup] = useState(false);

  async function fetchData() {
    setLoading(true);
    try {
      const rStats = await fetch('/api/stats');
      setStats(await rStats.json());
      
      const rApps = await fetch('/api/applications');
      setApps(await rApps.json());
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, []);

  const handleUpdateStatus = async (jobId: number, newStatus: string) => {
    try {
      const r = await fetch(`/api/applications/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (r.ok) {
        fetchData();
        if (selectedApp && selectedApp.job_id === jobId) {
          setSelectedApp((prev: Application | null) => prev ? { ...prev, status: newStatus } : null);
        }
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleSaveNotes = async () => {
    if (!selectedApp) return;
    try {
      const r = await fetch(`/api/applications/${selectedApp.job_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: notesInput }),
      });
      if (r.ok) {
        fetchData();
        setSelectedApp((prev: Application | null) => prev ? { ...prev, notes: notesInput } : null);
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleGenerateFollowup = async (app: Application, seq: number) => {
    setGeneratingFollowup(true);
    setFollowupDraft(null);
    try {
      const days = seq === 1 ? 7 : (seq === 2 ? 14 : 21);
      const r = await fetch(`/api/outreach/${app.job_id}/generate?followup_number=${seq}&days_since_apply=${days}`);
      const data = await r.json();
      setFollowupDraft({
        seq,
        subject: data.subject,
        body: data.body,
        job_id: app.job_id,
        company: app.company,
        title: app.title
      });
    } catch (e: any) {
      console.error(e);
    } finally {
      setGeneratingFollowup(false);
    }
  };

  const handleSaveOutreachLog = async () => {
    if (!followupDraft) return;
    try {
      const r = await fetch('/api/outreach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: followupDraft.job_id,
          subject: followupDraft.subject,
          body: followupDraft.body,
          channel: 'clipboard',
          status: 'sent_manually'
        })
      });
      if (r.ok) {
        setFollowupDraft(null);
        alert('Outreach follow-up logged successfully.');
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const openAppDetails = (app: Application) => {
    setSelectedApp(app);
    setNotesInput(app.notes || '');
    setStatusSelect(app.status);
    setFollowupDraft(null);
  };

  const COLUMNS = ['Saved', 'Tailored', 'Applied', 'Interview', 'Offer', 'Rejected'];

  const getStaleApplications = () => {
    const fourteenDaysAgo = new Date();
    fourteenDaysAgo.setDate(fourteenDaysAgo.getDate() - 14);
    
    return apps.filter(a => {
      if (a.status !== 'Applied') return false;
      const updated = new Date(a.updated_at || a.created_at);
      return updated < fourteenDaysAgo;
    });
  };

  const staleApps = getStaleApplications();

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-16 pt-4 px-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <BarChart3 className="text-gray-400" size={24} />
            Tracker
          </h1>
          <p className="text-sm text-muted mt-1">Kanban board for application statuses.</p>
        </div>
        <button onClick={fetchData} disabled={loading} className="btn-minimal flex items-center gap-2">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh Board
        </button>
      </div>

      {/* KPI Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="surface-panel p-4 h-24 flex flex-col justify-between">
            <span className="text-xs text-muted uppercase tracking-wider">Response Rate</span>
            <div className="text-2xl font-semibold text-emerald-500">{stats.response_rate}%</div>
          </div>
          <div className="surface-panel p-4 h-24 flex flex-col justify-between">
            <span className="text-xs text-muted uppercase tracking-wider">Avg Match Score</span>
            <div className="text-2xl font-semibold text-white">{stats.avg_score}/10</div>
          </div>
          <div className="surface-panel p-4 h-24 flex flex-col justify-between">
            <span className="text-xs text-muted uppercase tracking-wider">Best Channel</span>
            <div className="text-lg font-semibold text-blue-400 truncate">{stats.best_source || 'N/A'}</div>
          </div>
          <div className="surface-panel p-4 h-24 flex flex-col justify-between">
            <span className="text-xs text-muted uppercase tracking-wider">Active Pipeline</span>
            <div className="text-2xl font-semibold text-white">
              {stats.total_saved + stats.total_tailored + stats.total_applied + stats.total_interview}
            </div>
          </div>
        </div>
      )}

      {/* Stale Alerts */}
      {staleApps.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex gap-3 items-center">
            <AlertTriangle className="text-amber-400" size={18} />
            <div className="text-sm">
              <span className="font-semibold text-white">Stale Applications: </span>
              {staleApps.length} applications marked "Applied" for &gt;14 days. Send follow-ups.
            </div>
          </div>
          <div className="flex gap-2">
            {staleApps.slice(0, 2).map(sa => (
              <button key={sa.id} onClick={() => openAppDetails(sa)}
                className="btn-minimal bg-amber-500/20 border-transparent text-amber-200">
                Review {sa.company}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Kanban Board Grid */}
      <div className="flex gap-4 overflow-x-auto pb-4 items-start min-h-[600px]">
        {COLUMNS.map(col => {
          const colApps = apps.filter(a => a.status === col);
          
          return (
            <div key={col} className="flex flex-col w-[280px] shrink-0 bg-[#121214] border border-white/5 rounded-xl h-full pb-2">
              <div className="p-3 border-b border-white/5 flex justify-between items-center bg-[#18181b] rounded-t-xl mb-3">
                <span className="text-sm font-semibold text-white">{col}</span>
                <span className="text-xs text-muted bg-[#27272a] px-2 py-0.5 rounded-md">{colApps.length}</span>
              </div>

              <div className="px-2 space-y-2 overflow-y-auto max-h-[650px] custom-scrollbar">
                {colApps.map(a => (
                  <motion.div layout key={a.id} onClick={() => openAppDetails(a)}
                    className="p-3 bg-[#18181b] border border-white/5 rounded-lg hover:border-white/20 transition-all cursor-pointer">
                    <div className="flex justify-between items-start gap-2 mb-1">
                      <h4 className="text-sm font-medium text-white leading-tight break-words">{a.title}</h4>
                      {a.match_score && (
                        <span className="text-xs font-semibold text-blue-400 shrink-0">{a.match_score}</span>
                      )}
                    </div>
                    <p className="text-xs text-muted font-medium mb-3">{a.company}</p>
                    
                    {a.applied_at && (
                      <div className="flex items-center gap-1 text-[10px] text-gray-500">
                        <Clock size={12} /> Applied: {a.applied_at}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal Backdrop */}
      {selectedApp && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#09090b] border border-white/10 w-full max-w-2xl rounded-xl overflow-hidden flex flex-col max-h-[90vh] shadow-2xl">
            <div className="p-5 border-b border-white/10 flex justify-between items-center bg-[#121214]">
              <div>
                <h3 className="text-lg font-semibold text-white">{selectedApp.title}</h3>
                <p className="text-sm text-muted mt-1">{selectedApp.company}</p>
              </div>
              <button onClick={() => setSelectedApp(null)} className="text-gray-400 hover:text-white">
                <X size={20} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-medium text-muted mb-2 uppercase">Stage Status</label>
                  <select value={statusSelect} onChange={(e) => { setStatusSelect(e.target.value); handleUpdateStatus(selectedApp.job_id, e.target.value); }}
                    className="minimal-input w-full">
                    {COLUMNS.map(col => <option key={col} value={col}>{col}</option>)}
                    <option value="Closed">Closed</option>
                  </select>
                </div>
                
                {selectedApp.applied_at && (
                  <div>
                    <label className="block text-xs font-medium text-muted mb-2 uppercase">Timeline</label>
                    <div className="text-sm text-gray-300">
                      <div>Applied: <span className="text-white">{selectedApp.applied_at}</span></div>
                      {selectedApp.follow_up_at && <div>Followed up: <span className="text-white">{selectedApp.follow_up_at}</span></div>}
                    </div>
                  </div>
                )}
              </div>

              <div className="border-t border-white/10 pt-5">
                <h4 className="text-sm font-medium text-white flex items-center gap-2 mb-3">
                  <MessageSquare size={16} className="text-gray-400" />
                  Follow-Up Sequences
                </h4>
                <div className="flex gap-2">
                  <button onClick={() => handleGenerateFollowup(selectedApp, 1)} className="btn-minimal flex-1">Sequence #1 (7 Days)</button>
                  <button onClick={() => handleGenerateFollowup(selectedApp, 2)} className="btn-minimal flex-1">Sequence #2 (14 Days)</button>
                  <button onClick={() => handleGenerateFollowup(selectedApp, 3)} className="btn-minimal flex-1">Final Check-In</button>
                </div>

                {generatingFollowup && <div className="text-sm text-blue-400 mt-4 flex items-center gap-2"><RefreshCw size={14} className="animate-spin" /> Drafting...</div>}

                {followupDraft && (
                  <div className="mt-4 surface-panel p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-emerald-500 uppercase tracking-wide">Draft Ready</span>
                      <button onClick={handleSaveOutreachLog} className="text-sm text-blue-400 hover:text-white font-medium">Log as Sent</button>
                    </div>
                    <div className="text-sm text-white font-medium">Subj: {followupDraft.subject}</div>
                    <pre className="text-xs text-gray-300 font-mono bg-black p-3 rounded-md whitespace-pre-wrap">{followupDraft.body}</pre>
                  </div>
                )}
              </div>

              <div className="border-t border-white/10 pt-5 space-y-3">
                <label className="block text-xs font-medium text-muted uppercase">Application Notes</label>
                <textarea value={notesInput} onChange={(e) => setNotesInput(e.target.value)} rows={4}
                  className="minimal-input w-full resize-none" placeholder="Interview details, feedback, salary..." />
                <button onClick={handleSaveNotes} className="btn-primary flex items-center gap-2 px-4 py-2 ml-auto rounded-md">
                  <Save size={14} /> Save Notes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
