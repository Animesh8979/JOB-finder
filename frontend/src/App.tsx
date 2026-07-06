import React, { useState, useEffect, Suspense } from 'react';
import { Home, Search, Wand2, Play, BarChart2, Mail, AlertTriangle, ShieldCheck, Terminal, Menu, X, Loader2, Sparkles, Zap } from 'lucide-react';
import { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from './store/useAppStore';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import CinematicBackground from './components/CinematicBackground';

const queryClient = new QueryClient();

const Setup = React.lazy(() => import('./pages/Setup'));
const FindJobs = React.lazy(() => import('./pages/FindJobs'));
const Tailor = React.lazy(() => import('./pages/Tailor'));
const Apply = React.lazy(() => import('./pages/Apply'));
const Tracker = React.lazy(() => import('./pages/Tracker'));
const Outreach = React.lazy(() => import('./pages/Outreach'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));

const LoadingFallback = () => (
  <div className="w-full h-full flex items-center justify-center min-h-[50vh]">
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <Loader2 className="animate-spin text-indigo-400" size={28} />
        <div className="absolute inset-0 blur-lg bg-indigo-500/20 rounded-full" />
      </div>
      <span className="text-xs text-zinc-500 tracking-widest uppercase font-medium">Loading module…</span>
    </div>
  </div>
);

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  const { readiness, checkReadiness } = useAppStore();

  const { data: readinessData } = useQuery({
    queryKey: ['status'],
    queryFn: async () => {
      const res = await axios.get('/api/status');
      return res.data;
    },
    refetchInterval: 15000,
    refetchOnWindowFocus: true
  });

  useEffect(() => {
    if (readinessData) {
      useAppStore.setState({ readiness: readinessData });
    }
  }, [readinessData]);

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart2, category: 'CORE' },
    { id: 'setup', label: 'Profile & Setup', icon: Home, category: 'CORE' },
    { id: 'find', label: 'Job Inbox', icon: Search, category: 'DISCOVERY' },
    { id: 'tailor', label: 'AI Tailor', icon: Wand2, category: 'DISCOVERY' },
    { id: 'apply', label: 'Apply Engine', icon: Play, category: 'PIPELINE' },
    { id: 'tracker', label: 'Tracker', icon: BarChart2, category: 'PIPELINE' },
    { id: 'outreach', label: 'Outreach', icon: Mail, category: 'PIPELINE' }
  ];

  const categories = ['CORE', 'DISCOVERY', 'PIPELINE'];

  const renderContent = () => {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          className="w-full h-full"
          initial={{ opacity: 0, y: 12, filter: 'blur(6px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          exit={{ opacity: 0, y: -8, filter: 'blur(6px)' }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          <Suspense fallback={<LoadingFallback />}>
            {(() => {
              switch (activeTab) {
                case 'dashboard': return <Dashboard />;
                case 'setup': return <Setup onStatusChange={checkReadiness} />;
                case 'find': return <FindJobs />;
                case 'tailor': return <Tailor />;
                case 'apply': return <Apply />;
                case 'tracker': return <Tracker />;
                case 'outreach': return <Outreach />;
                default: return <Dashboard />;
              }
            })()}
          </Suspense>
        </motion.div>
      </AnimatePresence>
    );
  };

  const isSetupComplete = readiness.ai_key && readiness.resume && readiness.identity;
  const readyCount = [readiness.ai_key, readiness.resume, readiness.identity].filter(Boolean).length;

  return (
    <div className="flex min-h-screen bg-transparent text-slate-100 overflow-hidden font-sans relative selection:bg-indigo-500/30">
      <CinematicBackground />
      <Toaster position="top-right" toastOptions={{
        style: {
          background: 'rgba(12, 12, 14, 0.85)',
          backdropFilter: 'blur(20px)',
          color: '#fafafa',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          fontSize: '13px',
          borderRadius: '12px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.5), 0 0 32px -8px rgba(99, 102, 241, 0.15)',
        },
        success: {
          iconTheme: { primary: '#34d399', secondary: '#000' },
        },
        error: {
          style: { border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5', background: 'rgba(50, 10, 10, 0.85)' },
          iconTheme: { primary: '#f87171', secondary: '#000' }
        }
      }} />

      <div className="flex flex-col md:flex-row w-full h-screen p-0 md:p-3 gap-3 z-10">
        
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between p-4 border-b border-white/5 bg-[#030303]/85 backdrop-blur-2xl">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
              <Zap size={18} className="text-indigo-400" />
            </div>
            <div className="font-bold text-gradient-primary text-sm tracking-widest uppercase">Copilot</div>
          </div>
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-zinc-400 hover:text-white transition-colors">
            {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Sidebar */}
        <aside className={`
          ${isSidebarOpen ? 'flex' : 'hidden'} 
          md:flex 
          w-full md:w-[260px] glass-sidebar flex-col overflow-hidden
          absolute md:relative h-[calc(100vh-73px)] md:h-[calc(100vh-24px)] top-[73px] md:top-0 left-0 
          bg-[#030303]/92 md:bg-transparent backdrop-blur-2xl rounded-none md:rounded-2xl
          border-r md:border border-white/[0.04] shadow-2xl z-20
        `}>
          {/* Brand */}
          <div className="hidden md:flex p-5 pb-4 items-center gap-3 border-b border-white/[0.04]">
            <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500/15 to-purple-500/15 border border-white/[0.08] shadow-lg shadow-indigo-500/5">
              <Sparkles size={20} className="text-indigo-300" />
            </div>
            <div>
              <div className="font-bold text-gradient-primary text-base tracking-wide">AI Copilot</div>
              <div className="text-[10px] text-zinc-500 font-medium tracking-wider mt-0.5">JOB FINDER</div>
            </div>
          </div>

          {/* Status Capsule */}
          <div className="mx-3 my-4 p-3.5 rounded-xl bg-black/25 border border-white/[0.04] space-y-3">
            <div className="flex items-center justify-between text-[10px] mb-1">
              <span className="text-zinc-500 font-semibold uppercase tracking-wider">System</span>
              {isSetupComplete ? (
                <span className="text-emerald-400 flex items-center gap-1.5 font-bold">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-live" />
                  LIVE
                </span>
              ) : (
                <span className="text-amber-400 flex items-center gap-1.5 font-bold">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  {readyCount}/3
                </span>
              )}
            </div>
            
            {/* Mini progress bar */}
            <div className="h-1 w-full bg-zinc-800/80 rounded-full overflow-hidden">
              <motion.div 
                className="h-full rounded-full"
                style={{
                  background: isSetupComplete 
                    ? 'linear-gradient(90deg, #34d399, #10b981)' 
                    : 'linear-gradient(90deg, #fbbf24, #f59e0b)'
                }}
                initial={{ width: 0 }}
                animate={{ width: `${(readyCount / 3) * 100}%` }}
                transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>

            <div className="space-y-1.5 text-[10px] font-medium tracking-wide">
              {[
                { label: 'AI Provider', ok: readiness.ai_key },
                { label: 'Resume', ok: readiness.resume },
                { label: 'Identity', ok: readiness.identity },
              ].map(s => (
                <div key={s.label} className="flex items-center justify-between py-0.5">
                  <span className="text-zinc-500">{s.label}</span>
                  <span className={s.ok ? 'text-emerald-500' : 'text-zinc-600'}>
                    {s.ok ? '●' : '○'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-1 space-y-6 overflow-y-auto custom-scrollbar pb-8">
            {categories.map(cat => {
              const items = menuItems.filter(item => item.category === cat);
              return (
                <div key={cat} className="space-y-1">
                  <h4 className="text-[9px] font-bold text-zinc-600 uppercase tracking-[0.15em] px-3 mb-2">{cat}</h4>
                  <div className="space-y-0.5">
                    {items.map(item => {
                      const Icon = item.icon;
                      const isActive = activeTab === item.id;
                      return (
                        <button key={item.id} onClick={() => { setActiveTab(item.id); setIsSidebarOpen(false); }}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 text-[13px] font-medium transition-all rounded-xl relative overflow-hidden ${
                            isActive 
                              ? 'text-white bg-white/[0.06] border border-white/[0.06]' 
                              : 'text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.03] border border-transparent'
                          }`}>
                          {isActive && (
                            <motion.div 
                              layoutId="sidebar-active" 
                              className="absolute left-0 top-[20%] bottom-[20%] w-[3px] bg-indigo-400 rounded-r-full shadow-[0_0_12px_rgba(99,102,241,0.6)]" 
                              transition={{ type: "spring", stiffness: 400, damping: 30 }}
                            />
                          )}
                          <Icon size={16} className={isActive ? 'text-indigo-300' : 'text-zinc-600'} />
                          <span className="tracking-wide">{item.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-white/[0.03]">
            <div className="text-[10px] text-zinc-600 text-center tracking-wider font-medium">v2.0 • AI-Powered</div>
          </div>
        </aside>

        {/* Main Panel */}
        <main className="flex-1 overflow-y-auto bg-transparent relative z-10 custom-scrollbar rounded-2xl md:border border-white/[0.04] md:bg-[rgba(10,10,12,0.15)] md:backdrop-blur-sm md:shadow-[inset_0_0_24px_rgba(0,0,0,0.4)]">
          <div className="w-full h-full p-4 md:p-8">
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
