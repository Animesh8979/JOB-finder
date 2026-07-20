import React, { useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import BorderBeam from './BorderBeam';

interface QuestionItem {
  category: string;
  question: string;
  rationale?: string;
}

interface MockInterviewModalProps {
  jobId: number;
  jobTitle?: string;
  companyName?: string;
  onClose: () => void;
}

export const MockInterviewModal: React.FC<MockInterviewModalProps> = ({ jobId, jobTitle, companyName, onClose }) => {
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<number>(0);

  const handleGenerate = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/mock_interview/${jobId}?num_questions=4`);
      if (res.ok) {
        const data = await res.json();
        setQuestions(data.questions || []);
        toast.success('Interview questions generated offline!');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to generate mock interview.');
      }
    } catch {
      toast.error('Network error calling mock interview service.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative w-full max-w-2xl rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-2xl overflow-hidden"
      >
        <BorderBeam duration={10} size={200} color="#8b5cf6" />

        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6 relative z-10">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-indigo-400 animate-ping" />
              AI Mock Interview Copilot
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Simulating Principal HR & Tech Screener for <span className="text-indigo-300 font-semibold">{jobTitle || 'Role'}</span> at <span className="text-indigo-300 font-semibold">{companyName || 'Company'}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors text-sm"
          >
            ✕
          </button>
        </div>

        <div className="relative z-10 space-y-6">
          {questions.length === 0 && !loading ? (
            <div className="py-12 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto text-2xl">
                🎙️
              </div>
              <p className="text-sm text-slate-300 max-w-md mx-auto">
                Generate tailored technical and system design interview questions comparing your resume achievements against this job description.
              </p>
              <button
                onClick={handleGenerate}
                className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-950/40 transition-all"
              >
                Generate Interview Prep (Zero-Cost / Local)
              </button>
            </div>
          ) : loading ? (
            <div className="py-16 text-center space-y-3">
              <div className="inline-block w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
              <div className="text-sm font-medium text-slate-300">Analyzing skills & drafting deep-dive questions...</div>
              <div className="text-xs text-slate-500">Running on local provider ({questions.length} questions queued)</div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
                {questions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActiveTab(idx)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                      activeTab === idx ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-950/60 text-slate-400 hover:text-slate-200 border border-slate-800'
                    }`}
                  >
                    Q{idx + 1}: {q.category}
                  </button>
                ))}
              </div>

              {questions[activeTab] && (
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded-full border border-indigo-500/20">
                      {questions[activeTab].category} Question
                    </span>
                  </div>

                  <h4 className="text-lg font-semibold text-white leading-relaxed font-sans">
                    "{questions[activeTab].question}"
                  </h4>

                  {questions[activeTab].rationale && (
                    <div className="bg-slate-900/90 border border-slate-800/80 rounded-lg p-3 space-y-1">
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        Screener Rationale (Why they ask this):
                      </div>
                      <p className="text-xs text-slate-300 italic">
                        {questions[activeTab].rationale}
                      </p>
                    </div>
                  )}
                </motion.div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={handleGenerate}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors"
                >
                  Regenerate Questions
                </button>
                <button
                  onClick={onClose}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow transition-colors"
                >
                  Done Practicing
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default MockInterviewModal;
