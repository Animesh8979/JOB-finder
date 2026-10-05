import React, { useState } from 'react';
import {
  Shield,
  Zap,
  Radar,
  Crosshair,
  GitPullRequest,
  Users,
  Code2,
  FileCheck2,
  Clock,
  TrendingUp,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Play,
  Copy,
  ExternalLink,
  ChevronRight,
  Terminal,
  Activity,
  Layers,
  Sparkles,
  Globe,
  Bot,
  Workflow,
  RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

type SubModule =
  | 'system_one'
  | 'radar'
  | 'forensics'
  | 'tournament'
  | 'trojan'
  | 'ats_efi'
  | 'backchannel'
  | 'skills'
  | 'interview_hud'
  | 'pacing'
  | 'evolution'
  | 'browser_agent'
  | 'career_orchestrator';

export default function ApexWarfareCenter() {
  const [activeModule, setActiveModule] = useState<SubModule>('system_one');

  // Sub-state for System-1
  const [sys1Query, setSys1Query] = useState('Senior Distributed Systems Engineer (Kafka, Rust, ClickHouse)');
  const [sys1Candidates, setSys1Candidates] = useState('Staff Infra Engineer\nFrontend React Dev\nDevOps Lead\nData Analyst');
  const [sys1Result, setSys1Result] = useState<any>(null);
  const [sys1Loading, setSys1Loading] = useState(false);

  // Sub-state for Predictive Radar
  const [radarCompany, setRadarCompany] = useState('Vercel');
  const [radarResult, setRadarResult] = useState<any>(null);
  const [radarLoading, setRadarLoading] = useState(false);

  // Sub-state for Forensics
  const [forensicTitle, setForensicTitle] = useState('Staff Distributed Systems Engineer');
  const [forensicCompany, setForensicCompany] = useState('TechCorp');
  const [forensicDesc, setForensicDesc] = useState('Fast-paced agile team looking for a rockstar developer with 10+ years experience in everything.');
  const [forensicDays, setForensicDays] = useState(75);
  const [forensicReposts, setForensicReposts] = useState(4);
  const [forensicResult, setForensicResult] = useState<any>(null);
  const [forensicLoading, setForensicLoading] = useState(false);

  // Sub-state for Tournament
  const [tournJd, setTournJd] = useState('Required: Kubernetes, Go, Kafka, Distributed Consensus, High-Throughput OLAP.');
  const [tournResume, setTournResume] = useState('Built distributed telemetry engine processing 200k ops/sec with Go and Kafka. Managed Kubernetes clusters.');
  const [tournResult, setTournResult] = useState<any>(null);
  const [tournLoading, setTournLoading] = useState(false);

  // Sub-state for Trojan Horse
  const [trojanCompany, setTrojanCompany] = useState('Stripe');
  const [trojanRepo, setTrojanRepo] = useState('stripe-python');
  const [trojanSkills, setTrojanSkills] = useState('Python, AsyncIO, Distributed Rate Limiting');
  const [trojanResult, setTrojanResult] = useState<any>(null);
  const [trojanLoading, setTrojanLoading] = useState(false);

  // Sub-state for ATS EFI
  const [efiText, setEfiText] = useState('John Doe | john@example.com | (555) 123-4567\nEXPERIENCE\nSenior Software Engineer at Google\n- Optimized query execution\nTECHNICAL SKILLS\nPython, Go, Kafka, Docker');
  const [efiKeywords, setEfiKeywords] = useState('python, go, kafka, docker, distributed systems');
  const [efiResult, setEfiResult] = useState<any>(null);
  const [efiLoading, setEfiLoading] = useState(false);

  // Sub-state for Backchannel
  const [bcCompany, setBcCompany] = useState('Datadog');
  const [bcRole, setBcRole] = useState('Staff Engineer');
  const [bcDomain, setBcDomain] = useState('datadoghq.com');
  const [bcResult, setBcResult] = useState<any>(null);
  const [bcLoading, setBcLoading] = useState(false);

  // Sub-state for Skill Scaffolder
  const [scaffoldSkill, setScaffoldSkill] = useState('Kafka');
  const [scaffoldResult, setScaffoldResult] = useState<any>(null);
  const [scaffoldLoading, setScaffoldLoading] = useState(false);

  // Sub-state for Interview HUD
  const [hudTranscript, setHudTranscript] = useState('Can you tell me about a time when a critical microservice failed in production and how you handled it?');
  const [hudResult, setHudResult] = useState<any>(null);
  const [hudLoading, setHudLoading] = useState(false);

  // Sub-state for Pacing & Game Theory
  const [pacingResult, setPacingResult] = useState<any>(null);
  const [pacingLoading, setPacingLoading] = useState(false);

  // Sub-state for Evolution
  const [evolutionResult, setEvolutionResult] = useState<any>(null);

  // Sub-state for Browser Agent
  const [browserJobUrl, setBrowserJobUrl] = useState('https://boards.greenhouse.io/stripe/jobs/12345');
  const [browserAutoSubmit, setBrowserAutoSubmit] = useState(false);
  const [browserResult, setBrowserResult] = useState<any>(null);
  const [browserLoading, setBrowserLoading] = useState(false);

  // Sub-state for Career Orchestrator
  const [orchestratorMode, setOrchestratorMode] = useState<'conservative' | 'autonomous' | 'full_auto'>('autonomous');
  const [orchestratorResult, setOrchestratorResult] = useState<any>(null);
  const [orchestratorLoading, setOrchestratorLoading] = useState(false);

  // Handlers
  const runBrowserApply = async () => {
    setBrowserLoading(true);
    try {
      const res = await axios.post('/api/v2/browser/apply', {
        job_url: browserJobUrl,
        auto_submit: browserAutoSubmit,
        profile_data: {
          name: 'Candidate User',
          email: 'candidate@example.com',
          skills: ['Go', 'Kafka', 'Distributed Systems', 'Python']
        }
      });
      setBrowserResult(res.data);
      toast.success(`Browser Agent status: ${res.data.status}`);
    } catch (e: any) {
      toast.error('Browser navigation failed: ' + e.message);
    } finally {
      setBrowserLoading(false);
    }
  };

  const runOrchestratorPipeline = async () => {
    setOrchestratorLoading(true);
    try {
      const sampleJobs = [
        {
          id: 101,
          company: 'Datadog',
          title: 'Senior Distributed Systems Engineer',
          url: 'https://careers.datadoghq.com/detail/101',
          description: 'High-throughput metrics streaming with Kafka, Go, p99 latency profiling, and microservices architecture.'
        },
        {
          id: 102,
          company: 'Revature',
          title: 'Associate Engineer',
          url: 'https://example.com/revature/102',
          description: 'Dynamic rockstar team-player wearing many hats in agile environment.'
        }
      ];
      const res = await axios.post('/api/v2/pipeline/run', {
        jobs: sampleJobs,
        mode: orchestratorMode,
        max_jobs_per_run: 2,
        profile_data: {
          name: 'Alex Vance',
          skills: ['Go', 'Kafka', 'PostgreSQL', 'Distributed Systems'],
          summary: 'Experienced distributed systems engineer with Go and Kafka.'
        }
      });
      setOrchestratorResult(res.data);
      toast.success(`Orchestrator run complete: ${res.data.applications_processed} processed!`);
    } catch (e: any) {
      toast.error('Pipeline failed: ' + e.message);
    } finally {
      setOrchestratorLoading(false);
    }
  };
  const runSystemOne = async () => {
    setSys1Loading(true);
    try {
      const candidates = sys1Candidates.split('\n').filter(c => c.trim().length > 0);
      const res = await axios.post('/api/v2/system-one/triage', { query: sys1Query, candidates });
      setSys1Result(res.data);
      toast.success(`System-1 resolved in ${res.data.latency_ms}ms!`);
    } catch (e: any) {
      toast.error('System-1 triage failed: ' + e.message);
    } finally {
      setSys1Loading(false);
    }
  };

  const runRadarScan = async () => {
    setRadarLoading(true);
    try {
      const res = await axios.post('/api/v2/radar/scan', {
        company_name: radarCompany,
        sec_form_d_filings: [{ filing_date: '2026-08-15', amount_raised_usd: 35000000 }],
        github_commit_signals: [{ repo: 'core-infra', tech_migrated_to: 'ClickHouse', commit_date: '2026-08-20' }],
        executive_hires: [{ title: 'VP of Engineering', start_date: '2026-08-01' }]
      });
      setRadarResult(res.data);
      toast.success('Pre-market radar scan complete!');
    } catch (e: any) {
      toast.error('Radar scan failed: ' + e.message);
    } finally {
      setRadarLoading(false);
    }
  };

  const runForensics = async () => {
    setForensicLoading(true);
    try {
      const res = await axios.post('/api/v2/forensics/audit', {
        title: forensicTitle,
        company: forensicCompany,
        description: forensicDesc,
        days_active: forensicDays,
        repost_count: forensicReposts
      });
      setForensicResult(res.data);
      toast.success('Forensic audit complete!');
    } catch (e: any) {
      toast.error('Forensics failed: ' + e.message);
    } finally {
      setForensicLoading(false);
    }
  };

  const runTournament = async () => {
    setTournLoading(true);
    try {
      const res = await axios.post('/api/v2/tournament/simulate', {
        job_description: tournJd,
        resume_text: tournResume,
        simulations: 50
      });
      setTournResult(res.data);
      toast.success('50-round Shadow Tournament completed!');
    } catch (e: any) {
      toast.error('Tournament failed: ' + e.message);
    } finally {
      setTournLoading(false);
    }
  };

  const runTrojan = async () => {
    setTrojanLoading(true);
    try {
      const skills = trojanSkills.split(',').map(s => s.trim());
      const res = await axios.post('/api/v2/trojan/synthesize', {
        target_company: trojanCompany,
        target_repo_or_product: trojanRepo,
        candidate_skills: skills,
        issue_description: 'High contention on distributed lock during checkout bursts'
      });
      setTrojanResult(res.data);
      toast.success('Trojan Horse PR Blueprint synthesized!');
    } catch (e: any) {
      toast.error('Trojan synthesis failed: ' + e.message);
    } finally {
      setTrojanLoading(false);
    }
  };

  const runEfi = async () => {
    setEfiLoading(true);
    try {
      const keywords = efiKeywords.split(',').map(k => k.trim());
      const res = await axios.post('/api/v2/ats/decompile', {
        resume_text: efiText,
        expected_keywords: keywords
      });
      setEfiResult(res.data);
      toast.success(`EFI Audit: ${(res.data.overall_efi * 100).toFixed(1)}%`);
    } catch (e: any) {
      toast.error('EFI audit failed: ' + e.message);
    } finally {
      setEfiLoading(false);
    }
  };

  const runBackchannel = async () => {
    setBcLoading(true);
    try {
      const res = await axios.post('/api/v2/backchannel/route', {
        company_name: bcCompany,
        target_role: bcRole,
        domain: bcDomain,
        candidate_profile: { name: 'Alex Mercer', skills: ['Distributed Systems', 'Go', 'Kafka'] },
        job_details: { company: bcCompany, title: bcRole }
      });
      setBcResult(res.data);
      toast.success('Backchannel route discovered!');
    } catch (e: any) {
      toast.error('Backchannel route failed: ' + e.message);
    } finally {
      setBcLoading(false);
    }
  };

  const runScaffold = async () => {
    setScaffoldLoading(true);
    try {
      const res = await axios.post('/api/v2/skills/scaffold', {
        candidate_skills: ['Python', 'SQL'],
        target_jobs: [{ title: 'Infra Lead', description: 'Requires Kafka, Kubernetes, Redis' }],
        scaffold_skill: scaffoldSkill
      });
      setScaffoldResult(res.data);
      toast.success(`Repository blueprint for ${scaffoldSkill} generated!`);
    } catch (e: any) {
      toast.error('Scaffolder failed: ' + e.message);
    } finally {
      setScaffoldLoading(false);
    }
  };

  const runHud = async () => {
    setHudLoading(true);
    try {
      const res = await axios.post('/api/v2/interview/hud', { transcript_snippet: hudTranscript });
      setHudResult(res.data);
      toast.success('Whisper HUD card generated!');
    } catch (e: any) {
      toast.error('HUD failed: ' + e.message);
    } finally {
      setHudLoading(false);
    }
  };

  const runPacing = async () => {
    setPacingLoading(true);
    try {
      const samplePackages = [
        {
          company: 'Acme Corp',
          stage: 'OFFER',
          base_salary: 175000,
          equity_annual_usd: 40000,
          signing_bonus: 25000,
          location: 'San Francisco',
          cost_of_living_index: 1.35,
          offer_deadline_iso: '2026-09-25',
          preference_rank: 2
        },
        {
          company: 'HyperScale AI',
          stage: 'FINAL_ROUND',
          base_salary: 190000,
          equity_annual_usd: 65000,
          signing_bonus: 30000,
          location: 'Remote',
          cost_of_living_index: 1.0,
          preference_rank: 1
        }
      ];
      const res = await axios.post('/api/v2/pacing/plan', { packages: samplePackages });
      setPacingResult(res.data);
      toast.success('Game theory pacing plan computed!');
    } catch (e: any) {
      toast.error('Pacing plan failed: ' + e.message);
    } finally {
      setPacingLoading(false);
    }
  };

  const loadEvolution = async () => {
    try {
      const res = await axios.get('/api/v2/evolution/status');
      setEvolutionResult(res.data);
      toast.success('Evolution ledger updated!');
    } catch (e: any) {
      toast.error('Evolution status failed: ' + e.message);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  return (
    <div className="flex flex-col h-full space-y-4 p-2 md:p-4 text-slate-100 font-sans">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between p-4 rounded-2xl bg-[#0c0c10]/95 border border-indigo-500/20 shadow-[0_8px_32px_rgba(0,0,0,0.5)] gap-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 p-[1px] flex items-center justify-center">
            <div className="w-full h-full bg-[#0c0c10] rounded-xl flex items-center justify-center text-indigo-400">
              <Shield size={24} className="animate-pulse" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black tracking-tight text-white uppercase font-mono">
                APEX CAREER AUTONOMOUS WARFARE ENGINE
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                v2.0 JEV-PARALLEL
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Sub-50ms System-1 Decisions • Pre-Market Radar • Shadow Tournaments • Trojan Dispatch • Interview Whisper HUD
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>BAYESIAN PRIOR: ACTIVE</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Cpu size={14} />
            <span>LATENCY: &lt; 50ms</span>
          </div>
        </div>
      </div>

      {/* Module Selector Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar text-xs font-mono">
        {[
          { id: 'system_one', label: '1. Jev System-1', icon: Zap },
          { id: 'radar', label: '2. Pre-Market Radar', icon: Radar },
          { id: 'forensics', label: '3. Ghost Forensics', icon: Crosshair },
          { id: 'tournament', label: '4. Shadow Tournament', icon: Users },
          { id: 'trojan', label: '5. Trojan Horse PR', icon: GitPullRequest },
          { id: 'ats_efi', label: '6. ATS EFI Verifier', icon: FileCheck2 },
          { id: 'backchannel', label: '7. Backchannel Path', icon: ExternalLink },
          { id: 'skills', label: '8. 48h Skill Scaffolder', icon: Code2 },
          { id: 'interview_hud', label: '9. Interview Whisper HUD', icon: Terminal },
          { id: 'pacing', label: '10. Offer Game Theory', icon: TrendingUp },
          { id: 'evolution', label: '11. Self-Evolution', icon: Sparkles },
          { id: 'browser_agent', label: '12. Stealth Browser Agent', icon: Globe },
          { id: 'career_orchestrator', label: '13. Master Orchestrator', icon: Workflow }
        ].map(m => {
          const Icon = m.icon;
          const isActive = activeModule === m.id;
          return (
            <button
              key={m.id}
              onClick={() => {
                setActiveModule(m.id as SubModule);
                if (m.id === 'evolution') loadEvolution();
              }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl whitespace-nowrap transition-all border ${
                isActive
                  ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-200 shadow-[0_0_16px_rgba(99,102,241,0.25)] font-bold'
                  : 'bg-[#121218]/60 border-white/[0.05] text-zinc-400 hover:text-zinc-200 hover:bg-[#161622]'
              }`}
            >
              <Icon size={14} className={isActive ? 'text-indigo-400' : 'text-zinc-500'} />
              <span>{m.label}</span>
            </button>
          );
        })}
      </div>

      {/* Workspace Area */}
      <div className="flex-1 min-h-[480px] p-4 rounded-2xl bg-[#0c0c10]/80 border border-white/[0.06] backdrop-blur-md overflow-y-auto">
        {/* MODULE 1: SYSTEM-1 */}
        {activeModule === 'system_one' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Zap size={18} className="text-yellow-400" /> Jev System-1 Parallel Decision Primitives
                </h3>
                <p className="text-xs text-zinc-400">
                  Sub-50ms non-autoregressive decision model (`Choice`, `Score`, `Noul`) with calibrated probability.
                </p>
              </div>
              <button
                onClick={runSystemOne}
                disabled={sys1Loading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 disabled:opacity-50"
              >
                {sys1Loading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>EXECUTE TRIAGE</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1">TARGET QUERY / REQUISITION</label>
                  <input
                    type="text"
                    value={sys1Query}
                    onChange={e => setSys1Query(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#14141d] border border-white/[0.08] text-white text-xs font-mono focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1">CANDIDATE OPTIONS (1 PER LINE)</label>
                  <textarea
                    rows={4}
                    value={sys1Candidates}
                    onChange={e => setSys1Candidates(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#14141d] border border-white/[0.08] text-white text-xs font-mono focus:border-indigo-500 outline-none resize-none"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs flex flex-col justify-between">
                <div>
                  <div className="text-zinc-500 text-[11px] mb-2 flex items-center justify-between">
                    <span>SYSTEM-1 OUTPUT TELEMETRY</span>
                    {sys1Result && <span className="text-emerald-400 font-bold">{sys1Result.latency_ms} ms</span>}
                  </div>
                  {sys1Result ? (
                    <div className="space-y-2">
                      <div className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-200">
                        <div className="text-[10px] text-indigo-400 font-bold">SELECTED OPTION (Index: {sys1Result.index})</div>
                        <div className="text-sm font-bold mt-1 text-white">{sys1Result.selected}</div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <div className="p-2 rounded-lg bg-black/40 border border-white/[0.04]">
                          <span className="text-zinc-500 text-[10px]">CALIBRATED P:</span>
                          <div className="text-emerald-400 font-bold text-sm">{(sys1Result.calibrated_p * 100).toFixed(1)}%</div>
                        </div>
                        <div className="p-2 rounded-lg bg-black/40 border border-white/[0.04]">
                          <span className="text-zinc-500 text-[10px]">EXECUTION MODE:</span>
                          <div className="text-purple-400 font-bold text-sm">{sys1Result.mode}</div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-zinc-600 text-center py-8">
                      Click "Execute Triage" to run instant sub-50ms candidate matching.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MODULE 2: PREDICTIVE RADAR */}
        {activeModule === 'radar' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Radar size={18} className="text-emerald-400 animate-spin" /> Pre-Market Hiring Requisition Radar
                </h3>
                <p className="text-xs text-zinc-400">
                  Detects unannounced job requisitions 14-30 days before public listing via SEC Form D, GitHub migrations, and executive hiring.
                </p>
              </div>
              <button
                onClick={runRadarScan}
                disabled={radarLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
              >
                {radarLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>SCAN PRE-MARKET SIGNALS</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] space-y-3 font-mono text-xs">
                <label className="block text-zinc-400 font-bold">COMPANY DOMAIN / NAME</label>
                <input
                  type="text"
                  value={radarCompany}
                  onChange={e => setRadarCompany(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[#1a1a26] border border-white/[0.08] text-white text-xs outline-none"
                />
                <div className="text-[11px] text-zinc-500 leading-relaxed">
                  Scanning public SEC Form D filings, public repository commit surges, and executive VP/Director transitions...
                </div>
              </div>

              <div className="md:col-span-2 p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2">RADAR INTELLIGENCE REPORT</div>
                {radarResult ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                      <div>
                        <div className="text-[10px] text-emerald-400 font-bold">PREDICTED HIRING WINDOW</div>
                        <div className="text-sm font-bold text-white">{radarResult.predicted_hiring_window}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] text-zinc-400">SIGNAL CONFIDENCE</div>
                        <div className="text-emerald-400 text-sm font-bold">{(radarResult.overall_confidence * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                    <div className="text-xs text-zinc-300">
                      <span className="text-zinc-500">Predicted Roles:</span> {radarResult.predicted_roles?.join(', ')}
                    </div>
                    <div className="p-3 rounded-lg bg-black/40 border border-white/[0.04] text-[11px] text-zinc-400 leading-relaxed">
                      {radarResult.rationale}
                    </div>
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-8">
                    Scan a company to identify hidden hiring pipelines before they hit LinkedIn.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 3: GHOST JOB FORENSICS */}
        {activeModule === 'forensics' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Crosshair size={18} className="text-red-400" /> Ghost Job & Intent Forensic Filter
                </h3>
                <p className="text-xs text-zinc-400">
                  Exposes ghost jobs, evergreen resume harvesters, and compliance listings before wasting candidate hours.
                </p>
              </div>
              <button
                onClick={runForensics}
                disabled={forensicLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-red-600/20 disabled:opacity-50"
              >
                {forensicLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>AUDIT INTENT</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-zinc-400 mb-1">JOB TITLE</label>
                    <input
                      type="text"
                      value={forensicTitle}
                      onChange={e => setForensicTitle(e.target.value)}
                      className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-zinc-400 mb-1">COMPANY</label>
                    <input
                      type="text"
                      value={forensicCompany}
                      onChange={e => setForensicCompany(e.target.value)}
                      className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-zinc-400 mb-1">DAYS ACTIVE</label>
                    <input
                      type="number"
                      value={forensicDays}
                      onChange={e => setForensicDays(Number(e.target.value))}
                      className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-zinc-400 mb-1">REPOST COUNT</label>
                    <input
                      type="number"
                      value={forensicReposts}
                      onChange={e => setForensicReposts(Number(e.target.value))}
                      className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-zinc-400 mb-1">DESCRIPTION SNIPPET</label>
                  <textarea
                    rows={3}
                    value={forensicDesc}
                    onChange={e => setForensicDesc(e.target.value)}
                    className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white resize-none"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2">FORENSIC VERDICT</div>
                {forensicResult ? (
                  <div className="space-y-3">
                    <div className={`p-3 rounded-lg border ${
                      forensicResult.is_ghost_job
                        ? 'bg-red-500/10 border-red-500/40 text-red-200'
                        : 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                    }`}>
                      <div className="text-[10px] font-bold">
                        {forensicResult.is_ghost_job ? 'FLAGGED: HIGH GHOST RISK' : 'VERIFIED: ACTIVE INTENT'}
                      </div>
                      <div className="text-sm font-bold mt-1">
                        Hiring Intent Score: {(forensicResult.hiring_intent_score * 100).toFixed(0)}%
                      </div>
                    </div>
                    {forensicResult.signals?.map((sig: any, idx: number) => (
                      <div key={idx} className="p-2 rounded bg-black/40 border border-white/[0.04] text-[11px] text-zinc-300">
                        <span className="text-red-400 font-bold">[{sig.signal_type}]</span> {sig.description}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-8">
                    Run audit to inspect ghost job probability and evergreen harvesting flags.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 4: SHADOW TOURNAMENT */}
        {activeModule === 'tournament' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Users size={18} className="text-purple-400" /> Adversarial Shadow Hiring Tournament
                </h3>
                <p className="text-xs text-zinc-400">
                  Runs 50-round Monte Carlo simulation across 3 adversarial personas: ATS, Cynical Recruiter, and EM.
                </p>
              </div>
              <button
                onClick={runTournament}
                disabled={tournLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-purple-600/20 disabled:opacity-50"
              >
                {tournLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>SIMULATE TOURNAMENT</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <label className="block text-zinc-400 mb-1">JOB DESCRIPTION REQUIREMENTS</label>
                  <textarea
                    rows={3}
                    value={tournJd}
                    onChange={e => setTournJd(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#14141d] border border-white/[0.08] text-white resize-none"
                  />
                </div>
                <div>
                  <label className="block text-zinc-400 mb-1">CANDIDATE RESUME PROFILE</label>
                  <textarea
                    rows={3}
                    value={tournResume}
                    onChange={e => setTournResume(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#14141d] border border-white/[0.08] text-white resize-none"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2">MONTE CARLO SIMULATION RESULTS</div>
                {tournResult ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
                        <div className="text-[10px] text-purple-400 font-bold">WIN RATE</div>
                        <div className="text-lg font-bold text-white">{(tournResult.win_rate * 100).toFixed(1)}%</div>
                      </div>
                      <div className="p-3 rounded-lg bg-black/40 border border-white/[0.04]">
                        <div className="text-[10px] text-zinc-400">BAYESIAN ALPHA / BETA</div>
                        <div className="text-emerald-400 font-bold text-sm">
                          α: {tournResult.bayesian_prior_alpha.toFixed(1)} | β: {tournResult.bayesian_prior_beta.toFixed(1)}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-zinc-300">
                      <span className="text-zinc-500">Fatal Disqualifiers:</span>{' '}
                      {tournResult.fatal_disqualifiers?.length > 0
                        ? tournResult.fatal_disqualifiers.join(', ')
                        : 'None detected! Resume passed adversarial filters.'}
                    </div>
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-8">
                    Run simulation to benchmark resume win rate across 50 Monte Carlo rounds.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 5: TROJAN HORSE */}
        {activeModule === 'trojan' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <GitPullRequest size={18} className="text-cyan-400" /> Proof-of-Value Trojan Horse Dispatch
                </h3>
                <p className="text-xs text-zinc-400">
                  Instead of a cold resume, synthesizes a concrete code patch, bug fix, or architecture blueprint for target engineering teams.
                </p>
              </div>
              <button
                onClick={runTrojan}
                disabled={trojanLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50"
              >
                {trojanLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>SYNTHESIZE TROJAN PR</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-zinc-400 mb-1">TARGET COMPANY</label>
                    <input
                      type="text"
                      value={trojanCompany}
                      onChange={e => setTrojanCompany(e.target.value)}
                      className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-zinc-400 mb-1">TARGET REPO / COMPONENT</label>
                    <input
                      type="text"
                      value={trojanRepo}
                      onChange={e => setTrojanRepo(e.target.value)}
                      className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-zinc-400 mb-1">CANDIDATE RELEVANT SKILLS</label>
                  <input
                    type="text"
                    value={trojanSkills}
                    onChange={e => setTrojanSkills(e.target.value)}
                    className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2">SYNTHESIZED PROOF-OF-VALUE DISPATCH</div>
                {trojanResult ? (
                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                      <div className="text-[10px] text-cyan-400 font-bold">TITLE</div>
                      <div className="text-sm font-bold text-white mt-1">{trojanResult.title}</div>
                    </div>
                    <div className="p-2.5 rounded bg-black/40 border border-white/[0.04] text-[11px] text-zinc-300">
                      <div className="text-zinc-500 font-bold mb-1">PITCH MEMO:</div>
                      <div className="whitespace-pre-wrap">{trojanResult.pitch_memo}</div>
                    </div>
                    <button
                      onClick={() => copyToClipboard(trojanResult.pitch_memo)}
                      className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 font-bold"
                    >
                      <Copy size={12} /> Copy Pitch Memo
                    </button>
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-8">
                    Synthesize an engineering-grade Proof-of-Value package to bypass standard recruiting gates.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 6: ATS EFI VERIFIER */}
        {activeModule === 'ats_efi' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <FileCheck2 size={18} className="text-emerald-400" /> Extraction Fidelity Index (EFI) Verifier
                </h3>
                <p className="text-xs text-zinc-400">
                  Simulates Workday, Taleo, and Greenhouse parsers. Enforces EFI &ge; 0.98 to eliminate parser drop-offs.
                </p>
              </div>
              <button
                onClick={runEfi}
                disabled={efiLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
              >
                {efiLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>VERIFY EFI SCORE</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <label className="block text-zinc-400 mb-1">RESUME TEXT (AS EXTRACTED BY ATS)</label>
                  <textarea
                    rows={5}
                    value={efiText}
                    onChange={e => setEfiText(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#14141d] border border-white/[0.08] text-white resize-none"
                  />
                </div>
                <div>
                  <label className="block text-zinc-400 mb-1">TARGET KEYWORDS</label>
                  <input
                    type="text"
                    value={efiKeywords}
                    onChange={e => setEfiKeywords(e.target.value)}
                    className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2">EXTRACTION FIDELITY REPORT</div>
                {efiResult ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                      <div>
                        <div className="text-[10px] text-emerald-400 font-bold">OVERALL EFI SCORE</div>
                        <div className="text-xl font-bold text-white">{(efiResult.overall_efi * 100).toFixed(1)}%</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] text-zinc-400">ATS SAFE?</div>
                        <div className={`font-bold text-sm ${efiResult.is_ats_safe ? 'text-emerald-400' : 'text-red-400'}`}>
                          {efiResult.is_ats_safe ? 'PASS (&ge; 98%)' : 'FAIL'}
                        </div>
                      </div>
                    </div>
                    {efiResult.issues?.map((iss: any, idx: number) => (
                      <div key={idx} className="p-2 rounded bg-black/40 border border-white/[0.04] text-[11px]">
                        <span className="text-amber-400 font-bold">[{iss.severity}]</span> {iss.description}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-8">
                    Verify extraction fidelity to prevent multi-column and encoding bugs in enterprise ATS.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 7: BACKCHANNEL PATHFINDER */}
        {activeModule === 'backchannel' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ExternalLink size={18} className="text-blue-400" /> Backchannel Org Graph Navigator
                </h3>
                <p className="text-xs text-zinc-400">
                  Maps engineering leadership, computes email permutations, and drafts Proof-of-Work memos.
                </p>
              </div>
              <button
                onClick={runBackchannel}
                disabled={bcLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-blue-600/20 disabled:opacity-50"
              >
                {bcLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>NAVIGATE BACKCHANNEL</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-zinc-400 mb-1">COMPANY NAME</label>
                    <input
                      type="text"
                      value={bcCompany}
                      onChange={e => setBcCompany(e.target.value)}
                      className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-zinc-400 mb-1">DOMAIN</label>
                    <input
                      type="text"
                      value={bcDomain}
                      onChange={e => setBcDomain(e.target.value)}
                      className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-zinc-400 mb-1">TARGET ROLE</label>
                  <input
                    type="text"
                    value={bcRole}
                    onChange={e => setBcRole(e.target.value)}
                    className="w-full p-2 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2">ORG GRAPH &amp; BACKCHANNEL MEMO</div>
                {bcResult ? (
                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-between">
                      <div>
                        <div className="text-[10px] text-blue-400 font-bold">PRIMARY BACKCHANNEL CONTACT</div>
                        <div className="text-sm font-bold text-white mt-0.5">{bcResult.primary_contact?.title}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] text-zinc-400">WARMTH SCORE</div>
                        <div className="text-blue-400 font-bold text-sm">{(bcResult.warmth_score * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                    {bcResult.memos?.slice(0, 1).map((memo: any, idx: number) => (
                      <div key={idx} className="p-2.5 rounded bg-black/40 border border-white/[0.04]">
                        <div className="text-[10px] text-zinc-500 font-bold">SUBJECT: {memo.subject}</div>
                        <div className="text-[11px] text-zinc-300 mt-1 whitespace-pre-wrap">{memo.body_text}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-8">
                    Discover direct engineering decision-makers and generate verified email permutations.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 8: 48H SKILL SCAFFOLDER */}
        {activeModule === 'skills' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Code2 size={18} className="text-amber-400" /> 48-Hour Proof-of-Competency Repository Scaffolder
                </h3>
                <p className="text-xs text-zinc-400">
                  Synthesizes production-grade GitHub repository blueprints to prove real competency instead of fake resume lines.
                </p>
              </div>
              <button
                onClick={runScaffold}
                disabled={scaffoldLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-amber-600/20 disabled:opacity-50"
              >
                {scaffoldLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>SCAFFOLD REPO BLUEPRINT</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <label className="block text-zinc-400 mb-1">SELECT HIGH-ROI SKILL TO SCAFFOLD</label>
                  <select
                    value={scaffoldSkill}
                    onChange={e => setScaffoldSkill(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#14141d] border border-white/[0.08] text-white"
                  >
                    <option value="kafka">Kafka (Distributed Event Stream Pipeline)</option>
                    <option value="kubernetes">Kubernetes (Zero-Downtime Microservice GitOps)</option>
                    <option value="clickhouse">ClickHouse (OLAP Real-Time Telemetry Engine)</option>
                    <option value="redis">Redis (Distributed Sliding-Window Token Bucket)</option>
                  </select>
                </div>
                <div className="text-[11px] text-zinc-400 leading-relaxed">
                  Generates full project architecture, ready-to-run unit tests with pytest, automated GitHub Actions CI workflow, and architectural README with benchmarks.
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2">GENERATED REPOSITORY BLUEPRINT</div>
                {scaffoldResult?.blueprint ? (
                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                      <div className="text-[10px] text-amber-400 font-bold">PROJECT NAME</div>
                      <div className="text-sm font-bold text-white mt-0.5">{scaffoldResult.blueprint.project_name}</div>
                      <div className="text-[11px] text-zinc-300 mt-1">{scaffoldResult.blueprint.headline}</div>
                    </div>
                    <div className="text-[11px] text-zinc-400">
                      Files Generated: {scaffoldResult.blueprint.files?.length} files (including CI workflow &amp; tests)
                    </div>
                    <div className="p-2.5 rounded bg-black/40 border border-white/[0.04] text-[11px] text-emerald-400">
                      Verification Command: {scaffoldResult.blueprint.verification_command}
                    </div>
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-8">
                    Select a skill and scaffold a 48-hour repository blueprint.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 9: INTERVIEW WHISPER HUD */}
        {activeModule === 'interview_hud' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Terminal size={18} className="text-emerald-400" /> Real-Time Interview Whisper HUD
                </h3>
                <p className="text-xs text-zinc-400">
                  Sub-50ms live question matching. Instantly matches STAR+R stories, system design blueprints, and reverse questions.
                </p>
              </div>
              <button
                onClick={runHud}
                disabled={hudLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
              >
                {hudLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>PROCESS WHISPER</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 font-mono text-xs">
                <label className="block text-zinc-400 mb-1">LIVE INTERVIEWER TRANSCRIPT / AUDIO SNIPPET</label>
                <textarea
                  rows={4}
                  value={hudTranscript}
                  onChange={e => setHudTranscript(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[#14141d] border border-white/[0.08] text-white resize-none"
                />
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2">LIVE FLASHCARD &amp; ARCHITECTURE</div>
                {hudResult ? (
                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                      <div className="text-[10px] text-emerald-400 font-bold">{hudResult.category} • {hudResult.detected_intent}</div>
                      <div className="text-sm font-bold text-white mt-0.5">{hudResult.headline}</div>
                    </div>
                    <ul className="space-y-1">
                      {hudResult.talking_points?.map((tp: string, idx: number) => (
                        <li key={idx} className="text-[11px] text-zinc-300 flex items-start gap-1.5">
                          <span className="text-emerald-400">&bull;</span> {tp}
                        </li>
                      ))}
                    </ul>
                    {hudResult.architecture_snippet && (
                      <pre className="p-2 rounded bg-black/60 text-[10px] text-cyan-300 overflow-x-auto">
                        {hudResult.architecture_snippet}
                      </pre>
                    )}
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-8">
                    Input a question or audio snippet to render real-time response anchors.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 10: OFFER GAME THEORY */}
        {activeModule === 'pacing' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <TrendingUp size={18} className="text-amber-400" /> Multi-Pipeline Pacing &amp; Game Theory
                </h3>
                <p className="text-xs text-zinc-400">
                  Exploding offer defense, Compa-Ratio normalization, and counter-offer synchronization.
                </p>
              </div>
              <button
                onClick={runPacing}
                disabled={pacingLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-amber-600/20 disabled:opacity-50"
              >
                {pacingLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>CALCULATE LEVERAGE</span>
              </button>
            </div>

            <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
              <div className="text-zinc-500 text-[11px] mb-2">GAME-THEORETIC PACING &amp; NEGOTIATION ACTIONS</div>
              {pacingResult ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                      <div className="text-[10px] text-amber-400 font-bold">BATNA COMPANY</div>
                      <div className="text-sm font-bold text-white mt-0.5">{pacingResult.batna_company}</div>
                      <div className="text-xs text-zinc-300 mt-1">${pacingResult.batna_tc?.toLocaleString()} COL-adj TC</div>
                    </div>
                    <div className="p-3 rounded-lg bg-black/40 border border-white/[0.04]">
                      <div className="text-[10px] text-zinc-400">RESERVATION PRICE</div>
                      <div className="text-sm font-bold text-emerald-400 mt-0.5">${pacingResult.reservation_price?.toLocaleString()}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-black/40 border border-white/[0.04]">
                      <div className="text-[10px] text-zinc-400">STATUS</div>
                      <div className="text-sm font-bold text-purple-400 mt-0.5">SYNCHRONIZED</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-zinc-400 font-bold text-xs">RECOMMENDED PACING ACTIONS:</div>
                    {pacingResult.pacing_actions?.map((act: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-lg bg-[#181824] border border-white/[0.05] space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-amber-400 font-bold">{act.company} &bull; [{act.action_type}]</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                            act.urgency === 'CRITICAL' ? 'bg-red-500/20 text-red-300' : 'bg-blue-500/20 text-blue-300'
                          }`}>
                            {act.urgency}
                          </span>
                        </div>
                        <div className="text-zinc-300 text-[11px]">{act.recommended_action}</div>
                        <div className="p-2 rounded bg-black/50 text-zinc-400 text-[10px] whitespace-pre-wrap">
                          {act.email_template}
                        </div>
                        <button
                          onClick={() => copyToClipboard(act.email_template)}
                          className="flex items-center gap-1 text-[10px] text-indigo-400 hover:text-indigo-300 font-bold"
                        >
                          <Copy size={11} /> Copy Template
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-zinc-600 text-center py-8">
                  Click "Calculate Leverage" to optimize competing offer timelines and generate stall/accelerate scripts.
                </div>
              )}
            </div>
          </div>
        )}

        {/* MODULE 11: RECURSIVE SELF-EVOLUTION */}
        {activeModule === 'evolution' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Sparkles size={18} className="text-purple-400" /> Recursive Codebase Self-Evolution Ledger
                </h3>
                <p className="text-xs text-zinc-400">
                  Continuous learning loops that synthesize, sandbox-verify, and integrate new tools and filter patches.
                </p>
              </div>
              <button
                onClick={loadEvolution}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-purple-600/20"
              >
                <RefreshCw size={14} />
                <span>REFRESH LEDGER</span>
              </button>
            </div>

            <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
              <div className="text-zinc-500 text-[11px] mb-2">PERSISTENT EVOLUTION LEDGER</div>
              {evolutionResult ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
                      <div className="text-[10px] text-purple-400 font-bold">TOTAL LESSONS LEARNED</div>
                      <div className="text-lg font-bold text-white mt-0.5">{evolutionResult.total_lessons_learned}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-black/40 border border-white/[0.04]">
                      <div className="text-[10px] text-zinc-400">PATCHES SYNTHESIZED</div>
                      <div className="text-lg font-bold text-emerald-400 mt-0.5">{evolutionResult.total_patches_synthesized}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-black/40 border border-white/[0.04]">
                      <div className="text-[10px] text-zinc-400">SANDBOX VERIFIED</div>
                      <div className="text-lg font-bold text-blue-400 mt-0.5">{evolutionResult.verified_patches}</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-zinc-400 font-bold text-xs">RECENT SYNTHESIZED LESSONS:</div>
                    {evolutionResult.recent_lessons?.length > 0 ? (
                      evolutionResult.recent_lessons.map((les: any, idx: number) => (
                        <div key={idx} className="p-2.5 rounded bg-black/40 border border-white/[0.04] text-[11px]">
                          <div className="text-purple-400 font-bold">[{les.trigger_source}] {les.observation}</div>
                          <div className="text-zinc-400 text-[10px] mt-1">Action: {les.action_taken}</div>
                        </div>
                      ))
                    ) : (
                      <div className="text-zinc-600">No evolutionary lessons recorded yet. The system learns continuously from runtime traces.</div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-zinc-600 text-center py-8">
                  Loading autonomous evolution ledger...
                </div>
              )}
            </div>
          </div>
        )}

        {/* MODULE 12: STEALTH BROWSER AGENT */}
        {activeModule === 'browser_agent' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Globe size={18} className="text-cyan-400" /> Stealth Browser Agent & Easy Apply Navigator
                </h3>
                <p className="text-xs text-zinc-400">
                  Perceive-plan-act loop with Camoufox anti-detect transport and indexed LLM form manifest fill.
                </p>
              </div>
              <button
                onClick={runBrowserApply}
                disabled={browserLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50"
              >
                {browserLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>LAUNCH NAVIGATOR</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <label className="block text-zinc-400 mb-1">TARGET APPLICATION URL</label>
                  <input
                    type="text"
                    value={browserJobUrl}
                    onChange={e => setBrowserJobUrl(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#14141d] border border-white/[0.08] text-white focus:border-cyan-500 outline-none"
                  />
                </div>
                <div className="p-3 rounded-xl bg-[#14141d] border border-white/[0.08] flex items-center justify-between">
                  <div>
                    <div className="text-white font-bold">Auto-Submit Mode</div>
                    <div className="text-[10px] text-zinc-500">When disabled, stops safely at review stage.</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={browserAutoSubmit}
                    onChange={e => setBrowserAutoSubmit(e.target.checked)}
                    className="w-4 h-4 rounded text-cyan-600 focus:ring-0"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#14141e] border border-white/[0.08] font-mono text-xs">
                <div className="text-zinc-500 text-[11px] mb-2 flex items-center justify-between">
                  <span>EXECUTION LOG</span>
                  {browserResult && <span className="text-cyan-400 font-bold">{browserResult.status}</span>}
                </div>
                {browserResult ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2.5 rounded-lg bg-black/40 border border-white/[0.04]">
                        <div className="text-[10px] text-zinc-500">STEPS EXECUTED</div>
                        <div className="text-lg font-bold text-white mt-0.5">{browserResult.steps_executed}</div>
                      </div>
                      <div className="p-2.5 rounded-lg bg-black/40 border border-white/[0.04]">
                        <div className="text-[10px] text-zinc-500">FIELDS FILLED</div>
                        <div className="text-lg font-bold text-cyan-400 mt-0.5">{browserResult.fields_filled}</div>
                      </div>
                    </div>
                    <div className="p-2.5 rounded bg-black/40 border border-white/[0.04] text-[11px] text-zinc-300">
                      {browserResult.snapshot_summary}
                    </div>
                  </div>
                ) : (
                  <div className="text-zinc-600 text-center py-10">
                    Awaiting target application launch...
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MODULE 13: MASTER ORCHESTRATOR */}
        {activeModule === 'career_orchestrator' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Workflow size={18} className="text-emerald-400" /> Master Career Warfare Orchestrator
                </h3>
                <p className="text-xs text-zinc-400">
                  Full 8-stage pipeline: Discovery → Forensics → Matching → Tournament → Nav → Telemetry.
                </p>
              </div>
              <button
                onClick={runOrchestratorPipeline}
                disabled={orchestratorLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
              >
                {orchestratorLoading ? <Clock size={14} className="animate-spin" /> : <Play size={14} />}
                <span>RUN PIPELINE</span>
              </button>
            </div>

            <div className="space-y-4 font-mono text-xs">
              <div className="flex items-center gap-3 p-3 rounded-xl bg-[#14141d] border border-white/[0.08]">
                <span className="text-zinc-400">PIPELINE EXECUTION MODE:</span>
                {(['conservative', 'autonomous', 'full_auto'] as const).map(mode => (
                  <button
                    key={mode}
                    onClick={() => setOrchestratorMode(mode)}
                    className={`px-3 py-1.5 rounded-lg uppercase text-[11px] font-bold transition-all ${
                      orchestratorMode === mode
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : 'bg-black/30 text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>

              {orchestratorResult && (
                <div className="space-y-3">
                  <div className="grid grid-cols-4 gap-2">
                    <div className="p-3 rounded-xl bg-black/40 border border-white/[0.04]">
                      <div className="text-[10px] text-zinc-500">EVALUATED</div>
                      <div className="text-base font-bold text-white mt-0.5">{orchestratorResult.total_jobs_evaluated}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-black/40 border border-white/[0.04]">
                      <div className="text-[10px] text-zinc-500">PASSED FORENSICS</div>
                      <div className="text-base font-bold text-emerald-400 mt-0.5">{orchestratorResult.jobs_passed_forensics}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-black/40 border border-white/[0.04]">
                      <div className="text-[10px] text-zinc-500">TAILORED</div>
                      <div className="text-base font-bold text-indigo-400 mt-0.5">{orchestratorResult.jobs_tailored}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-black/40 border border-white/[0.04]">
                      <div className="text-[10px] text-zinc-500">APPLIED</div>
                      <div className="text-base font-bold text-cyan-400 mt-0.5">{orchestratorResult.applications_processed}</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-zinc-400 font-bold">REQUISITION FUNNEL REPORTS:</div>
                    {orchestratorResult.reports?.map((rep: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-xl bg-[#14141e] border border-white/[0.06] flex items-center justify-between">
                        <div>
                          <div className="text-white font-bold text-sm flex items-center gap-2">
                            <span>{rep.title} @ {rep.company}</span>
                            {rep.navigation_status === 'CAPTCHA_DETECTED' && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                                ACTION REQUIRED: SOLVE CAPTCHA
                              </span>
                            )}
                            {rep.navigation_status === 'LOGIN_REQUIRED' && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                                ACTION REQUIRED: SIGN IN
                              </span>
                            )}
                            {rep.navigation_status === 'SUCCESS' && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                AUTO-SUBMITTED
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-zinc-400 mt-0.5 flex items-center gap-3">
                            <span>Status: <span className="text-cyan-400">{rep.navigation_status}</span></span>
                            <span>| Strategy: <span className="text-indigo-400">{rep.selected_strategy_arm}</span></span>
                            {rep.fields_filled > 0 && <span>| Filled: <span className="text-emerald-400">{rep.fields_filled} inputs</span></span>}
                            {rep.url && (
                              <a
                                href={rep.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-cyan-400 hover:text-cyan-300 underline font-bold"
                              >
                                Open Portal &rarr;
                              </a>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            rep.is_ghost_job ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          }`}>
                            {rep.is_ghost_job ? 'GHOST JOB' : 'VERIFIED'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
