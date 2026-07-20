import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import BorderBeam from './BorderBeam';

interface OutreachItem {
  id: number;
  contact_name?: string;
  contact_email?: string;
  subject: string;
  body: string;
  channel: string;
  status: string;
  created_at: string;
}

export const OutreachQueue: React.FC = () => {
  const [items, setItems] = useState<OutreachItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<string>('draft');


  useEffect(() => {
    let active = true;
    fetch('/api/outreach')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (active && Array.isArray(data)) setItems(data);
      })
      .catch((err) => console.error('Failed to fetch outreach queue', err))
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleAction = async (id: number, action: 'approve' | 'reject', email?: string, subject?: string, body?: string) => {
    try {
      const res = await fetch(`/api/outreach/${id}/${action}`, { method: 'POST' });
      if (res.ok) {
        toast.success(action === 'approve' ? 'Outreach approved!' : 'Outreach rejected.');
        if (action === 'approve' && email) {
          const mailto = `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(subject || '')}&body=${encodeURIComponent(body || '')}`;
          window.open(mailto, '_blank');
        }
        setItems((prev) => prev.map((item) => (item.id === id ? { ...item, status: action === 'approve' ? 'approved' : 'rejected' } : item)));
      } else {
        toast.error(`Failed to ${action} outreach item.`);
      }
    } catch {
      toast.error('Network error during action.');
    }
  };

  const filteredItems = items.filter((i) => (filter === 'all' ? true : i.status === filter));

  return (
    <div className="relative rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl p-6 shadow-2xl overflow-hidden my-6">
      <BorderBeam duration={12} size={150} color="#10b981" />
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            HITL Outreach Approval Queue
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            Human-in-the-Loop guardrail: review AI-generated cold intros before opening in your mail client.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-950/60 p-1 rounded-lg border border-slate-800">
          {(['draft', 'approved', 'rejected', 'all'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1 rounded-md text-xs font-semibold capitalize transition-all ${
                filter === tab ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab} ({items.filter((i) => (tab === 'all' ? true : i.status === tab)).length})
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-500 animate-pulse text-sm">Loading queue...</div>
      ) : filteredItems.length === 0 ? (
        <div className="py-12 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
          No outreach items with status "{filter}".
        </div>
      ) : (
        <div className="space-y-4 relative z-10">
          <AnimatePresence>
            {filteredItems.map((item) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-700 transition-colors"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-base">To: {item.contact_name || 'Recruiter'}</span>
                    <span className="text-xs text-slate-400">({item.contact_email || 'no email listed'})</span>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                      item.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      item.status === 'rejected' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                      'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}>
                      {item.status}
                    </span>
                  </div>
                  <div className="text-sm font-medium text-emerald-300/90">Subject: {item.subject}</div>
                  <p className="text-xs text-slate-300 line-clamp-3 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 font-mono">
                    {item.body}
                  </p>
                </div>

                {item.status === 'draft' && (
                  <div className="flex sm:flex-col gap-2 shrink-0">
                    <button
                      onClick={() => handleAction(item.id, 'approve', item.contact_email, item.subject, item.body)}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-emerald-900/20 transition-all flex items-center justify-center gap-1.5"
                    >
                      Approve & Send
                    </button>
                    <button
                      onClick={() => handleAction(item.id, 'reject')}
                      className="px-4 py-2 bg-slate-900 hover:bg-rose-950/60 hover:text-rose-300 text-slate-400 text-xs font-semibold rounded-lg border border-slate-800 hover:border-rose-800/60 transition-all"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default OutreachQueue;
