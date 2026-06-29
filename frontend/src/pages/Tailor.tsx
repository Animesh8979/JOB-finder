/* eslint-disable @typescript-eslint/no-explicit-any */
import { Application } from '../types';
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { FileText, Wand2, Download, AlertTriangle, CheckCircle, Info, RefreshCw, File, Copy, Check, Sparkles } from 'lucide-react';


export default function Tailor() {
  const [apps, setApps] = useState<Application[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);

  // Tailoring params
  const [angle, setAngle] = useState('Balanced (Default)');
  const [tone, setTone] = useState('Professional');
  const [extraNotes, setExtraNotes] = useState('');

  // Results
  
  const [clText, setClText] = useState('');
  const [flaggedSkills, setFlaggedSkills] = useState<string[]>([]);
  const [files, setFiles] = useState<Record<string, any> | null>(null);

  // ATS & Bullet Improver Tabs
  const [activeTab, setActiveTab] = useState('docs'); // 'docs' | 'ats' | 'bullets'
  const [atsReport, setAtsReport] = useState<Record<string, any> | null>(null);
  const [loadingAts, setLoadingAts] = useState(false);
  const [bulletSuggestions, setBulletSuggestions] = useState<Application[]>([]);
  const [loadingBullets, setLoadingBullets] = useState(false);
  const [acceptedBullets, setAcceptedBullets] = useState<Record<number, boolean>>({});

  // Loading
  const [loading, setLoading] = useState(false);
  const [loadingApps, setLoadingApps] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  async function fetchApps() {
    setLoadingApps(true);
    try {
      const r = await fetch('/api/applications');
      const data = await r.json();
      setApps(data);
      if (data.length > 0 && !selectedJobId) {
        handleSelectApp(data[0].job_id);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchApps();
  }, []);

  async function handleSelectApp(jobId: number) {
    setSelectedJobId(jobId);
    
    setClText('');
    setFlaggedSkills([]);
    setFiles(null);
    setAtsReport(null);
    setBulletSuggestions([]);
    setAcceptedBullets({});
    setActiveTab('docs');
    setMessage({ text: '', type: '' });

    try {
      const r = await fetch(`/api/applications/${jobId}`);
      const data = await r.json();
      setAppDetail(data);
      if (data.cover_letter_text) {
        setClText(data.cover_letter_text);
      }
      if (data.tailored_resume_path) {
        // If files exist, set placeholder paths for download
        // We reconstruct them based on backend conventions
        setFiles({
          resume_pdf: `/api/files/download?path=${data.tailored_resume_path}`,
          cover_pdf: `/api/files/download?path=${data.cover_letter_path}`,
          resume_docx: `/api/files/download?path=${data.tailored_resume_path.replace('.pdf', '.docx')}`,
          cover_docx: `/api/files/download?path=${data.cover_letter_path.replace('.pdf', '.docx')}`,
        });
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleTailor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedJobId) return;

    setLoading(true);
    const tId = toast.loading('AI is tailoring your resume & cover letter (this may take 20-30 seconds)...');
    try {
      const r = await fetch(`/api/applications/${selectedJobId}/tailor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ angle, tone, extra_notes: extraNotes })
      });
      const data = await r.json();
      if (r.ok) {
        setClText(data.cover_letter_text);
        setFlaggedSkills(data.flagged_skills || []);
        setFiles(data.files);
        toast.success('AI Tailoring complete! Review customized documents.', { id: tId });
        fetchApps(); // Reload to update status icon on selector
      } else {
        toast.error(data.detail || 'Tailoring failed.', { id: tId });
      }
    } catch (err: any) {
      toast.error(`Error: ${err.message}`, { id: tId });
    } finally {
      setLoading(false);
    }
  };

  const handleRunAtsCheck = async () => {
    if (!selectedJobId) return;
    setLoadingAts(true);
    const tId = toast.loading('Simulating Applicant Tracking System (ATS) scan...');
    try {
      const r = await fetch(`/api/applications/${selectedJobId}/ats-check`, { method: 'POST' });
      const data = await r.json();
      if (r.ok) {
        setAtsReport(data);
        toast.success('ATS scan complete! Compatibility score calculated.', { id: tId });
      } else {
        toast.error(data.detail || 'ATS Check failed.', { id: tId });
      }
    } catch (err: any) {
      toast.error(`Error: ${err.message}`, { id: tId });
    } finally {
      setLoadingAts(false);
    }
  };

  const handleRunBulletImprover = async () => {
    if (!selectedJobId) return;
    setLoadingBullets(true);
    const tId = toast.loading('Generating AI rephrasing suggestions for experience bullets...');
    try {
      const r = await fetch(`/api/applications/${selectedJobId}/improve-bullets`, { method: 'POST' });
      const data = await r.json();
      if (r.ok) {
        setBulletSuggestions(data.suggestions || []);
        toast.success('Resume bullet suggestions ready!', { id: tId });
      } else {
        toast.error(data.detail || 'Bullet improvements failed.', { id: tId });
      }
    } catch (err: any) {
      toast.error(`Error: ${err.message}`, { id: tId });
    } finally {
      setLoadingBullets(false);
    }
  };

  const handleSaveCoverLetter = async () => {
    if (!selectedJobId) return;
    const tId = toast.loading('Saving cover letter edits...');
    try {
      const r = await fetch(`/api/applications/${selectedJobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cover_letter_text: clText })
      });
      if (r.ok) {
        toast.success('Cover letter edits saved!', { id: tId });
      } else {
        toast.error('Failed to save cover letter edits.', { id: tId });
      }
    } catch (e: any) {
      toast.error(`Error: ${e.message}`, { id: tId });
    }
  };

  const selectedApp = apps.find(a => a.job_id === selectedJobId);

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="border-b border-white/10 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          <FileText className="text-indigo-400" size={28} />
          Tailor Resume & Cover Letter
        </h1>
        <p className="text-gray-400 mt-1">Optimize documents for ATS compatibility based on job description keywords.</p>
      </div>

      {/* Selector Row */}
      <div className="surface-panel p-6 rounded-2xl flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="w-full md:max-w-md">
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Choose Application</label>
          {loadingApps ? (
            <div className="text-sm text-gray-400">Loading saved jobs...</div>
          ) : apps.length === 0 ? (
            <div className="text-sm text-amber-300">No applications saved. Go to "Find Jobs" to save.</div>
          ) : (
            <select value={selectedJobId || ''} onChange={(e) => handleSelectApp(parseInt(e.target.value))}
              className="w-full bg-neutral-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all">
              {apps.map(a => (
                <option key={a.job_id} value={a.job_id}>
                  [{a.status}] {a.company} — {a.title}
                </option>
              ))}
            </select>
          )}
        </div>

        {selectedApp && (
          <div className="text-right self-stretch md:self-center bg-white/5 md:bg-transparent p-4 md:p-0 rounded-xl">
            <span className="text-xs text-gray-400">Selected Match Score:</span>
            <div className="text-xl font-bold text-white mt-1">{selectedApp.match_score ? `${selectedApp.match_score}/10` : 'Unscored'}</div>
          </div>
        )}
      </div>

      {selectedJobId && selectedApp && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Settings Parameters */}
          <div className="lg:col-span-1 space-y-6">
            <div className="surface-panel p-6 rounded-2xl space-y-4">
              <h3 className="text-md font-semibold text-white flex items-center gap-2">
                <Wand2 size={18} className="text-indigo-400" />
                Tailoring Config
              </h3>
              
              <form onSubmit={handleTailor} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Resume Focus Angle</label>
                  <select value={angle} onChange={(e) => setAngle(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all">
                    <option value="Balanced (Default)">Balanced (Default)</option>
                    <option value="Skills-Focused">Skills-Focused (Hard tech skills)</option>
                    <option value="Leadership-Focused">Leadership-Focused (Management & strategy)</option>
                    <option value="Quantified-Metrics">Quantified-Metrics (Highlight numbers/scale)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Cover Letter Tone</label>
                  <select value={tone} onChange={(e) => setTone(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all">
                    <option value="Professional">Professional (Default)</option>
                    <option value="Enthusiastic">Enthusiastic (High interest)</option>
                    <option value="Technical">Technical (Detail-focused)</option>
                    <option value="Direct">Direct & Concise</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Extra instructions (e.g. weave in AWS/React)</label>
                  <textarea value={extraNotes} onChange={(e) => setExtraNotes(e.target.value)} rows={4}
                    className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all resize-none"
                    placeholder="Mention specific projects or align with their core values..." />
                </div>

                <button type="submit" disabled={loading}
                  className="w-full btn-primary font-semibold rounded-xl px-5 py-4 text-xs transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2">
                  {loading ? <RefreshCw className="animate-spin" size={16} /> : <Wand2 size={16} />}
                  Generate Tailored Docs
                </button>
              </form>
            </div>
          </div>

          {/* Results Display */}
          <div className="lg:col-span-2 space-y-6">
            {/* Tabs Selector */}
            <div className="flex border-b border-white/10 gap-6">
              <button type="button" onClick={() => setActiveTab('docs')}
                className={`pb-3 text-sm font-semibold transition-all border-b-2 -mb-0.5 ${
                  activeTab === 'docs' ? 'text-indigo-400 border-indigo-400' : 'text-gray-400 border-transparent hover:text-white'
                }`}>
                📄 Tailored Documents
              </button>
              <button type="button" onClick={() => setActiveTab('ats')}
                className={`pb-3 text-sm font-semibold transition-all border-b-2 -mb-0.5 ${
                  activeTab === 'ats' ? 'text-indigo-400 border-indigo-400' : 'text-gray-400 border-transparent hover:text-white'
                }`}>
                🤖 ATS Check
              </button>
              <button type="button" onClick={() => setActiveTab('bullets')}
                className={`pb-3 text-sm font-semibold transition-all border-b-2 -mb-0.5 ${
                  activeTab === 'bullets' ? 'text-indigo-400 border-indigo-400' : 'text-gray-400 border-transparent hover:text-white'
                }`}>
                ✍️ Bullet Optimizer
              </button>
            </div>

            {/* Notifications inside results column */}
            {message.text && (
              <div className={`p-4 rounded-xl flex items-center gap-3 border ${
                message.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' :
                message.type === 'error' ? 'bg-rose-500/10 border-rose-500/30 text-rose-300' :
                'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
              }`}>
                <Info size={18} className="shrink-0" />
                <span className="text-xs font-medium">{message.text}</span>
              </div>
            )}

            {/* Docs Tab */}
            {activeTab === 'docs' && (
              <div className="space-y-6">
                {flaggedSkills.length > 0 && (
                  <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-6 space-y-3">
                    <h3 className="text-md font-semibold text-rose-300 flex items-center gap-2">
                      <AlertTriangle size={20} />
                      ATS Fabrication Warning
                    </h3>
                    <p className="text-xs text-rose-300/80">
                      The AI added the following skills to match the job description, but they could **not** be verified in your base resume. Verify these are accurate before applying:
                    </p>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {flaggedSkills.map(skill => (
                        <span key={skill} className="text-[11px] bg-rose-500/20 text-rose-200 border border-rose-500/30 px-2 py-0.5 rounded capitalize font-medium">{skill}</span>
                      ))}
                    </div>
                  </div>
                )}

                {files ? (
                  <div className="surface-panel p-6 rounded-2xl space-y-4">
                    <h3 className="text-md font-semibold text-white flex items-center gap-2">
                      <Download className="text-indigo-400" size={18} />
                      Download Customized Documents
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="border border-white/5 rounded-xl p-4 bg-white/[0.01] flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-semibold text-white">Tailored Resume</h4>
                          <p className="text-[11px] text-gray-500 mt-0.5">ATS-Optimized format</p>
                        </div>
                        <div className="flex gap-2">
                          <a href={files.resume_docx} download className="p-2 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all">
                            <File size={14} /> DOCX
                          </a>
                          <a href={files.resume_pdf} download className="p-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all">
                            <FileText size={14} /> PDF
                          </a>
                        </div>
                      </div>

                      <div className="border border-white/5 rounded-xl p-4 bg-white/[0.01] flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-semibold text-white">Tailored Cover Letter</h4>
                          <p className="text-[11px] text-gray-500 mt-0.5">Ready to print/attach</p>
                        </div>
                        <div className="flex gap-2">
                          <a href={files.cover_docx} download className="p-2 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all">
                            <File size={14} /> DOCX
                          </a>
                          <a href={files.cover_pdf} download className="p-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all">
                            <FileText size={14} /> PDF
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="surface-panel rounded-2xl p-8 text-center backdrop-blur-xl">
                    <FileText className="mx-auto text-gray-500 mb-3" size={40} />
                    <h3 className="text-sm font-semibold text-white">No customized documents generated yet</h3>
                    <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">Select a Focus Angle and click "Generate Tailored Docs" on the left to begin.</p>
                  </div>
                )}

                {clText && (
                  <div className="surface-panel p-6 rounded-2xl space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-md font-semibold text-white">Cover Letter Review</h3>
                      <button onClick={handleSaveCoverLetter}
                        className="bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-medium px-3 py-1.5 rounded-lg text-xs transition-all active:scale-95">
                        Save Edits
                      </button>
                    </div>
                    <textarea value={clText} onChange={(e) => setClText(e.target.value)} rows={12}
                      className="w-full surface-panel rounded-xl p-4 text-white focus:outline-none focus:border-indigo-500 text-sm font-mono leading-relaxed transition-all" />
                  </div>
                )}
              </div>
            )}

            {/* ATS Check Tab */}
            {activeTab === 'ats' && (
              <div className="space-y-6">
                {atsReport ? (
                  <div className="space-y-6">
                    {/* Score Card */}
                    <div className="surface-panel p-6 rounded-2xl flex flex-col md:flex-row gap-6 items-center">
                      <div className="relative shrink-0 flex items-center justify-center">
                        <div className={`w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center ${
                          atsReport.ats_score >= 75 ? 'border-emerald-500 text-emerald-400 bg-emerald-500/5' :
                          atsReport.ats_score >= 50 ? 'border-amber-500 text-amber-400 bg-amber-500/5' :
                          'border-rose-500 text-rose-400 bg-rose-500/5'
                        }`}>
                          <span className="text-3xl font-extrabold">{atsReport.ats_score}</span>
                          <span className="text-[10px] font-bold uppercase tracking-wider">ATS Score</span>
                        </div>
                      </div>
                      <div className="space-y-2 text-center md:text-left">
                        <h4 className="text-base font-bold text-white">Simulated ATS Compatibility Result</h4>
                        <p className="text-xs text-gray-300 leading-relaxed max-w-md">
                          {atsReport.semantic_match.explanation}
                        </p>
                        <button onClick={handleRunAtsCheck} disabled={loadingAts}
                          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 mt-1 transition-all mx-auto md:mx-0">
                          <RefreshCw size={12} className={loadingAts ? 'animate-spin' : ''} />
                          Re-scan resume
                        </button>
                      </div>
                    </div>

                    {/* Heuristics metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Readability & Structure */}
                      <div className="surface-panel p-5 rounded-2xl space-y-4">
                        <div className="flex justify-between items-center border-b border-white/5 pb-2">
                          <h4 className="text-xs font-bold uppercase text-gray-400 tracking-wider">Readability & Sections</h4>
                          <span className={`text-xs font-bold ${atsReport.readability.score >= 75 ? 'text-emerald-400' : 'text-amber-400'}`}>{atsReport.readability.score}/100</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Word Count:</span>
                            <span className="font-semibold text-white">{atsReport.readability.word_count} words</span>
                          </div>
                          <div>
                            <span className="text-gray-400 block mb-1.5">Detected Sections:</span>
                            <div className="flex flex-wrap gap-1.5">
                              {atsReport.readability.sections_found.map((s: string) => (
                                <span key={s} className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-medium flex items-center gap-1">
                                  <Check size={10} /> {s}
                                </span>
                              ))}
                              {atsReport.readability.sections_missing.map((s: string) => (
                                <span key={s} className="bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded text-[10px] font-medium">
                                  ⚠️ Missing {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Achievements & Metrics */}
                      <div className="surface-panel p-5 rounded-2xl space-y-4">
                        <div className="flex justify-between items-center border-b border-white/5 pb-2">
                          <h4 className="text-xs font-bold uppercase text-gray-400 tracking-wider">Impact & Achievements</h4>
                          <span className={`text-xs font-bold ${atsReport.impact.score >= 75 ? 'text-emerald-400' : 'text-amber-400'}`}>{atsReport.impact.score}/100</span>
                        </div>
                        <div className="space-y-3 text-xs text-gray-300">
                          <div className="flex justify-between items-center">
                            <span>Quantified Metrics Detected:</span>
                            <span className="surface-panel px-2.5 py-1 rounded-lg font-bold text-white text-xs">{atsReport.impact.quantified_metrics_count}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span>Power Action Verbs:</span>
                            <span className="surface-panel px-2.5 py-1 rounded-lg font-bold text-white text-xs">{atsReport.impact.action_verbs_count}</span>
                          </div>
                          {atsReport.impact.metric_examples.length > 0 && (
                            <div className="text-[11px] bg-black/20 p-2.5 rounded-lg border border-white/5">
                              <span className="font-semibold text-indigo-300 block mb-1">Impact Highlight:</span>
                              <span className="italic text-gray-400">"{atsReport.impact.metric_examples[0]}"</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Keyword Density List */}
                    <div className="surface-panel p-6 rounded-2xl space-y-4">
                      <h4 className="text-xs font-bold uppercase text-gray-400 tracking-wider border-b border-white/5 pb-2">Keyword Density Analysis</h4>
                      
                      <div className="space-y-4">
                        <div>
                          <span className="text-xs text-emerald-400 font-semibold block mb-2">Matched Keywords ({atsReport.keywords.matched.length})</span>
                          {atsReport.keywords.matched.length === 0 ? (
                            <span className="text-xs text-gray-500 italic">No exact matches found.</span>
                          ) : (
                            <div className="flex flex-wrap gap-1.5">
                              {atsReport.keywords.matched.map((k: string) => (
                                <span key={k} className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-medium">{k}</span>
                              ))}
                            </div>
                          )}
                        </div>

                        <div>
                          <span className="text-xs text-rose-400 font-semibold block mb-2">Missing Keywords ({atsReport.keywords.missing.length})</span>
                          {atsReport.keywords.missing.length === 0 ? (
                            <span className="text-xs text-gray-500 italic">Excellent keyword coverage! No missing terms.</span>
                          ) : (
                            <div className="flex flex-wrap gap-1.5">
                              {atsReport.keywords.missing.map((k: string) => (
                                <span key={k} className="bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded text-[10px] font-medium">{k}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Semantic Match Suggestions */}
                    <div className="surface-panel p-6 rounded-2xl space-y-3">
                      <h4 className="text-xs font-bold uppercase text-gray-400 tracking-wider border-b border-white/5 pb-2 flex items-center gap-1.5">
                        <Sparkles size={14} className="text-indigo-400" />
                        AI Optimization Recommendations
                      </h4>
                      <ul className="list-disc pl-5 text-xs text-gray-300 space-y-2 leading-relaxed">
                        {atsReport.semantic_match.suggestions.map((s: string, idx: number) => (
                          <li key={idx}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="surface-panel rounded-2xl p-10 text-center backdrop-blur-xl space-y-4">
                    <Sparkles className="mx-auto text-gray-500" size={44} />
                    <div className="space-y-1">
                      <h3 className="text-sm font-semibold text-white">Simulate Applicant Tracking System Review</h3>
                      <p className="text-xs text-gray-400 max-w-sm mx-auto leading-relaxed">
                        Assess keyword density, structural formatting, quantified achievements, and semantic alignment exactly like Workday, Greenhouse, and Lever recruiters do.
                      </p>
                    </div>
                    <button onClick={handleRunAtsCheck} disabled={loadingAts}
                      className="mx-auto bg-indigo-500 hover:bg-indigo-600 text-white font-semibold rounded-xl px-5 py-3 text-xs transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2 shadow-lg shadow-indigo-500/15">
                      {loadingAts ? <RefreshCw className="animate-spin" size={12} /> : null}
                      Run ATS Compatibility Check
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Bullet Optimizer Tab */}
            {activeTab === 'bullets' && (
              <div className="space-y-6">
                {bulletSuggestions.length > 0 ? (
                  <div className="space-y-6">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-sm font-bold text-white">Interactive Resume Bullet Rephraser</h4>
                        <p className="text-xs text-gray-400 mt-0.5">Rewrite original achievements to feature missing keywords without exaggerating.</p>
                      </div>
                      <button onClick={handleRunBulletImprover} disabled={loadingBullets}
                        className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-all shrink-0">
                        <RefreshCw size={12} className={loadingBullets ? 'animate-spin' : ''} />
                        Re-analyze
                      </button>
                    </div>

                    <div className="space-y-4">
                      {bulletSuggestions.map((item: Record<string, any>, idx: number) => {
                        const isAccepted = !!acceptedBullets[idx];
                        
                        return (
                          <div key={idx} className="border border-white/5 bg-white/[0.01] rounded-2xl p-5 space-y-4 relative overflow-hidden transition-all">
                            {/* Card Header */}
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest bg-indigo-500/10 px-2 py-0.5 rounded">
                                Bullet Rewrite #{idx + 1}
                              </span>
                              {isAccepted && (
                                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest bg-emerald-500/10 px-2 py-0.5 rounded flex items-center gap-1">
                                  <CheckCircle size={10} /> Accepted
                                </span>
                              )}
                            </div>

                            {/* Side-by-Side Comparison */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {/* Original */}
                              <div className="space-y-1">
                                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">Original Bullet</span>
                                <div className={`text-xs leading-relaxed transition-all ${isAccepted ? 'text-gray-600 line-through' : 'text-gray-400'}`}>
                                  {item.original}
                                </div>
                              </div>

                              {/* Rewritten */}
                              <div className="space-y-1">
                                <span className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider block">Suggested Rewrite</span>
                                <div className="text-xs text-white leading-relaxed font-semibold">
                                  {item.suggested}
                                </div>
                              </div>
                            </div>

                            {/* Reasoning */}
                            <div className="text-[10px] text-gray-400 border-t border-white/5 pt-3 leading-normal flex items-start gap-1">
                              <Info size={12} className="shrink-0 mt-0.5 text-indigo-400" />
                              <span><em>ATS Rationale:</em> {item.explanation}</span>
                            </div>

                            {/* Action Row */}
                            <div className="flex justify-end gap-3 pt-1">
                              <button 
                                onClick={() => {
                                  navigator.clipboard.writeText(item.suggested);
                                  setMessage({ text: `Copied suggestion #${idx + 1} to clipboard!`, type: 'success' });
                                }}
                                className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95"
                              >
                                <Copy size={12} /> Copy to Clipboard
                              </button>
                              
                              <button 
                                onClick={() => {
                                  setAcceptedBullets(prev => ({ ...prev, [idx]: !prev[idx] }));
                                }}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95 ${
                                  isAccepted 
                                    ? 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-300' 
                                    : 'bg-indigo-500 hover:bg-indigo-600 text-white shadow-lg shadow-indigo-500/15'
                                }`}
                              >
                                {isAccepted ? 'Undo Accept' : 'Accept Suggestion'}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="surface-panel rounded-2xl p-10 text-center backdrop-blur-xl space-y-4">
                    <Wand2 className="mx-auto text-gray-500" size={44} />
                    <div className="space-y-1">
                      <h3 className="text-sm font-semibold text-white">Experience Bullet Point Rephraser</h3>
                      <p className="text-xs text-gray-400 max-w-sm mx-auto leading-relaxed">
                        Automatically optimize your experience bullets to contextually insert missing keywords and action verbs. Enforces zero hallucination guidelines.
                      </p>
                    </div>
                    <button onClick={handleRunBulletImprover} disabled={loadingBullets}
                      className="mx-auto bg-indigo-500 hover:bg-indigo-600 text-white font-semibold rounded-xl px-5 py-3 text-xs transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2 shadow-lg shadow-indigo-500/15">
                      {loadingBullets ? <RefreshCw className="animate-spin" size={12} /> : null}
                      Analyze & Improve Bullet Points
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
