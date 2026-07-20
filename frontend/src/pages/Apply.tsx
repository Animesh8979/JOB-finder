/* eslint-disable @typescript-eslint/no-explicit-any */
import { Application, Job } from '../types';
import React, { useState, useEffect } from 'react';
import { Play, Info, Copy, ClipboardCheck, AlertTriangle, AlertCircle, FileCheck, ExternalLink } from 'lucide-react';

export default function Apply() {
  const [apps, setApps] = useState<Application[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [appDetail, setAppDetail] = useState<Application | null>(null);
  const [jobDetail, setJobDetail] = useState<Job | null>(null);

  const [loading, setLoading] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [message, setMessage] = useState({ text: '', type: '' });

  async function fetchApps() {
    try {
      const r = await fetch('/api/applications');
      const data = await r.json();
      setApps(data);
      if (data.length > 0 && !selectedJobId) {
        handleSelectApp(data[0].job_id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchApps();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSelectApp(jobId: number) {
    setSelectedJobId(jobId);
    setMessage({ text: '', type: '' });
    
    try {
      const rApp = await fetch(`/api/applications/${jobId}`);
      const dataApp = await rApp.json();
      setAppDetail(dataApp);
      
      const rJob = await fetch('/api/jobs');
      const dataJobs = await rJob.json();
      const job = dataJobs.find((j: Job) => j.id === jobId);
      setJobDetail(job);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleLaunchApply = async () => {
    if (!selectedJobId) return;

    setLoading(true);
    setMessage({ text: 'Launching browser session...', type: 'info' });
    try {
      const r = await fetch(`/api/applications/${selectedJobId}/apply`, { method: 'POST' });
      const data = await r.json();
      if (r.ok) {
        setMessage({ text: data.note, type: 'success' });
      } else {
        setMessage({ text: data.detail || 'Browser launch failed.', type: 'error' });
      }
    } catch (err: any) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsApplied = async () => {
    if (!selectedJobId) return;

    const today = new Date();
    const followUp = new Date();
    followUp.setDate(today.getDate() + 7);

    try {
      const r = await fetch(`/api/applications/${selectedJobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'Applied',
          applied_at: today.toISOString().split('T')[0],
          follow_up_at: followUp.toISOString().split('T')[0]
        })
      });
      if (r.ok) {
        setMessage({ text: 'Application marked as applied!', type: 'success' });
        fetchApps();
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const getAnswerSheet = () => {
    if (!appDetail) return {};
    
    const resumeText = appDetail.tailored_resume_text || '';
    const nameMatch = resumeText.match(/^([^\n]+)/);
    const emailMatch = resumeText.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/);
    const phoneMatch = resumeText.match(/(\+?[0-9\s-]{8,15})/);

    const sheet: Record<string, any> = {
      'Full Name': nameMatch ? nameMatch[0].trim() : '',
      'Email Address': emailMatch ? emailMatch[0].trim() : '',
      'Phone Number': phoneMatch ? phoneMatch[0].trim() : '',
      'Cover Letter': appDetail.cover_letter_text || '',
    };
    
    return Object.fromEntries(Object.entries(sheet).filter(([, v]) => v));
  };

  const sheet = getAnswerSheet();
  const applyUrl = jobDetail?.apply_url || jobDetail?.url;
  const isGated = applyUrl && (applyUrl.includes('linkedin.com') || applyUrl.includes('indeed.com') || applyUrl.includes('glassdoor.com'));

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16 pt-4">
      {/* Header */}
      <div className="border-b border-white/5 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Play className="text-blue-500" size={24} />
          Apply
        </h1>
        <p className="text-sm text-muted mt-1">Review your tailored profile and execute autofill.</p>
      </div>

      <div className="surface-panel p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="w-full md:max-w-md">
          <label className="block text-xs font-medium text-muted uppercase mb-2">Select Application</label>
          <select value={selectedJobId || ''} onChange={(e) => handleSelectApp(parseInt(e.target.value))}
            className="minimal-input w-full">
            {apps.length === 0 ? <option value="">No active apps found</option> : null}
            {apps.map(a => (
              <option key={a.job_id} value={a.job_id}>
                [{a.status}] {a.company} — {a.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedJobId && jobDetail && appDetail && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <div className="surface-panel p-6 space-y-6">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Diagnostics</h3>

              <div className="space-y-1 border-t border-white/5 pt-4">
                <span className="text-xs text-muted uppercase block mb-2">Apply Link</span>
                <a href={applyUrl} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-400 hover:text-white transition-colors flex items-center gap-1.5 font-medium">
                  Open link in new tab <ExternalLink size={14} />
                </a>
              </div>

              <div className="space-y-2 border-t border-white/5 pt-4">
                <span className="text-xs text-muted uppercase block mb-2">Resume Status</span>
                {appDetail.tailored_resume_path ? (
                  <div className="flex items-center gap-2 text-sm text-emerald-500 font-medium">
                    <FileCheck size={16} /> Tailored resume generated
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-red-400 font-medium">
                    <AlertCircle size={16} /> Resume not tailored yet
                  </div>
                )}
              </div>

              {isGated && (
                <div className="bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded-lg p-3 flex gap-2 text-xs">
                  <AlertTriangle size={16} className="shrink-0" />
                  <div><strong>Gated Platform:</strong> Use manual copy/paste for this domain.</div>
                </div>
              )}

              {message.text && (
                <div className={`p-3 rounded-lg flex items-start gap-2 text-xs border ${
                  message.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                  message.type === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                  'bg-blue-500/10 border-blue-500/20 text-blue-400'
                }`}>
                  <Info size={14} className="shrink-0 mt-0.5" />
                  <span>{message.text}</span>
                </div>
              )}

              <div className="space-y-3 pt-4 border-t border-white/5">
                <button onClick={handleLaunchApply} disabled={loading}
                  className="w-full btn-primary px-4 py-3 text-sm flex items-center justify-center gap-2 rounded-md">
                  <Play size={16} /> Execute Autofill
                </button>
                <button onClick={handleMarkAsApplied}
                  className="w-full btn-minimal px-4 py-3 text-sm rounded-md">
                  Mark as Completed
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="surface-panel p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Data Sheet</h3>
              
              <div className="space-y-4 pt-4 border-t border-white/5">
                {Object.keys(sheet).length === 0 ? (
                  <div className="text-sm text-muted">Go to Tailor step first to generate data.</div>
                ) : (
                  Object.entries(sheet).map(([label, value]) => (
                    <div key={label} className="flex flex-col gap-2 bg-[#18181b] border border-[#27272a] rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-muted uppercase tracking-wider">{label}</span>
                        <button onClick={() => copyToClipboard(value, label)} className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1">
                          {copiedKey === label ? (
                            <><ClipboardCheck size={14} className="text-emerald-500" /> <span className="text-emerald-500">Copied!</span></>
                          ) : (
                            <><Copy size={14} /> <span>Copy</span></>
                          )}
                        </button>
                      </div>
                      
                      {label === 'Cover Letter' ? (
                        <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono mt-2 bg-black/50 p-3 rounded-md max-h-64 overflow-y-auto custom-scrollbar">
                          {value}
                        </pre>
                      ) : (
                        <div className="text-sm text-white font-medium select-all">{value}</div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
