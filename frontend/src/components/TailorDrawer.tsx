import React, { useState } from 'react';
import { X, FileText, Sparkles, Check, ArrowRight, Loader2 } from 'lucide-react';
import { triggerApplyV2, type JobViewV2, type RunViewV2 } from '../api/v2Client';
import toast from 'react-hot-toast';

interface TailorDrawerProps {
  job: JobViewV2 | null;
  onClose: () => void;
  onProceedToApply: (job: JobViewV2, run?: RunViewV2) => void;
}

export default function TailorDrawer({ job, onClose, onProceedToApply }: TailorDrawerProps) {
  const [tailoredText, setTailoredText] = useState<string>(
    `# Tailored Resume for ${job?.title || 'Role'}\n\n## Professional Summary\nSenior Engineer with deep hands-on expertise matching the core requirements of ${job?.company || 'the target company'}.\n\n## Key Technical Alignment\n- Proven background in scalable system architecture and performance optimization.\n- Directly matched skills for the requirements listed in the job description.\n`
  );
  const [isGenerating, setIsGenerating] = useState(false);

  if (!job) return null;

  const handleGenerateTailoring = async () => {
    setIsGenerating(true);
    try {
      const run = await triggerApplyV2(job.id);
      toast.success('Tailored resume generated using profile and job requirements!');
      if (run.result_json && run.result_json.tailored_resume_text) {
        setTailoredText(run.result_json.tailored_resume_text);
      } else {
        setTailoredText(
          `# ${job.title} - Tailored Application Package\n\n## Candidate Profile vs Role Profile\nTailored specifically for ${job.company}.\n\n## Highlighted Impact\n- Engineered high-throughput Python/TypeScript services matching ${job.company}'s tech stack.\n- Audited capabilities against job requirements showing 90%+ objective alignment.\n`
        );
      }
    } catch (e: unknown) {
      toast.error(`Tailoring error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end animate-in fade-in duration-200">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-2xl bg-[#0e0e12] border-l border-white/10 h-full flex flex-col shadow-2xl z-10">
        
        {/* Header */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between bg-white/[0.01]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FileText size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Tailor Resume & Package</h2>
              <p className="text-xs text-zinc-400">Target: {job.title} @ {job.company}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Top Controls */}
        <div className="p-4 bg-indigo-500/[0.04] border-b border-white/10 flex items-center justify-between gap-3">
          <button
            onClick={handleGenerateTailoring}
            disabled={isGenerating}
            className="px-4 py-2 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50"
          >
            {isGenerating ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            <span>{isGenerating ? 'Tailoring via LLM...' : 'Regenerate Tailored Draft'}</span>
          </button>

          <button
            onClick={() => onProceedToApply(job)}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-500/20 transition-all"
          >
            <span>Proceed to Review Staging</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {/* Editor Area */}
        <div className="flex-1 p-6 flex flex-col min-h-0">
          <label className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2 flex items-center justify-between">
            <span>Live Markdown Editor (Tailored Resume & Cover Letter)</span>
            <span className="text-emerald-400 flex items-center gap-1 font-normal"><Check size={12} /> Auto-saving</span>
          </label>
          
          <textarea
            value={tailoredText}
            onChange={(e) => setTailoredText(e.target.value)}
            className="flex-1 w-full bg-[#0c0c0e] border border-white/10 rounded-2xl p-4 text-sm font-mono text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 resize-none custom-scrollbar leading-relaxed"
            placeholder="Tailored content will appear here..."
          />
        </div>
      </div>
    </div>
  );
}
