import React, { useState, useEffect, Suspense } from 'react';
import { Home, Search, Wand2, Play, BarChart2, Mail, AlertTriangle, ShieldCheck, Terminal, Menu, X, Loader2 } from 'lucide-react';
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
    <Loader2 className="animate-spin text-blue-500" size={32} />
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
    { id: 'find', label: 'Inbox', icon: Search, category: 'DISCOVERY' },
    { id: 'tailor', label: 'Tailor', icon: Wand2, category: 'DISCOVERY' },
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
          initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          exit={{ opacity: 0, y: -10, filter: 'blur(4px)' }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
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

  return (
    <div className="flex min-h-screen bg-transparent text-slate-100 overflow-hidden font-sans relative selection:bg-blue-500/30">
      <CinematicBackground />
      <Toaster position="top-right" toastOptions={{
        style: {
          background: 'rgba(20, 20, 22, 0.8)',
          backdropFilter: 'blur(16px)',
          color: '#fafafa',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          fontSize: '13px',
          boxShadow: '0 16px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05)',
        },
        success: {
          iconTheme: { primary: '#34d399', secondary: '#000' },
        },
        error: {
          style: { border: '1px solid rgba(239, 68, 68, 0.4)', color: '#fca5a5', background: 'rgba(69, 10, 10, 0.8)' },
          iconTheme: { primary: '#f87171', secondary: '#000' }
        }
      }} />

      <div className="flex flex-col md:flex-row w-full h-screen p-0 md:p-4 gap-4 z-10">
        
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between p-4 border-b border-white/5 bg-[#050505]/80 backdrop-blur-2xl">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <Terminal size={18} className="text-blue-400" />
            </div>
            <div className="font-bold text-gradient text-sm tracking-widest uppercase">Copilot</div>
          </div>
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-gray-400 hover:text-white transition-colors">
            {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Sidebar Floating Island */}
        <aside className={`
          ${isSidebarOpen ? 'flex' : 'hidden'} 
          md:flex 
          w-full md:w-64 glass-sidebar flex-col overflow-hidden
          absolute md:relative h-[calc(100vh-73px)] md:h-[calc(100vh-32px)] top-[73px] md:top-0 left-0 
          bg-[#050505]/90 md:bg-[rgba(14,14,16,0.45)] backdrop-blur-2xl rounded-none md:rounded-2xl
          border-r md:border border-white/5 shadow-2xl z-20
        `}>
          {/* Title (Desktop) */}
          <div className="hidden md:flex p-6 items-center gap-3 border-b border-white/5 bg-white/[0.01]">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.2)]">
              <Terminal size={20} className="text-blue-300" />
            </div>
            <div className="font-bold text-gradient-primary text-lg tracking-wide">AI Copilot</div>
          </div>

          {/* Readiness */}
          <div className="mx-4 my-5 p-4 rounded-xl bg-black/20 border border-white/5 space-y-3 shadow-inner">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-gray-400 font-semibold uppercase tracking-wider">Status</span>
              {isSetupComplete ? (
                <span className="text-emerald-400 flex items-center gap-1 font-bold">
                  <ShieldCheck size={14} /> READY
                </span>
              ) : (
                <span className="text-red-400 flex items-center gap-1 font-bold">
                  <AlertTriangle size={14} /> PENDING
                </span>
              )}
            </div>
            
            <div className="space-y-2 text-[11px] font-medium tracking-wide">
              <div className="flex items-center justify-between">
                <span className="text-gray-500 uppercase">Provider</span>
                <span className={readiness.ai_key ? 'text-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.2)]' : 'text-red-500'}>{readiness.ai_key ? 'OK' : 'ERR'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500 uppercase">Resume</span>
                <span className={readiness.resume ? 'text-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.2)]' : 'text-red-500'}>{readiness.resume ? 'OK' : 'ERR'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500 uppercase">Identity</span>
                <span className={readiness.identity ? 'text-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.2)]' : 'text-red-500'}>{readiness.identity ? 'OK' : 'ERR'}</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-2 space-y-8 overflow-y-auto custom-scrollbar pb-10">
            {categories.map(cat => {
              const items = menuItems.filter(item => item.category === cat);
              return (
                <div key={cat} className="space-y-2">
                  <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest px-3 mb-3">{cat}</h4>
                  <div className="space-y-1">
                    {items.map(item => {
                      const Icon = item.icon;
                      const isActive = activeTab === item.id;
                      return (
                        <button key={item.id} onClick={() => { setActiveTab(item.id); setIsSidebarOpen(false); }}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium transition-all rounded-xl relative overflow-hidden ${
                            isActive 
                              ? 'text-white bg-white/10 shadow-sm border border-white/5' 
                              : 'text-gray-400 hover:text-white hover:bg-white/5'
                          }`}>
                          {isActive && (
                            <motion.div layoutId="sidebar-active" className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-blue-400 rounded-r-full shadow-[0_0_8px_#60a5fa]" />
                          )}
                          <Icon size={16} className={`${isActive ? 'text-blue-300' : 'text-gray-500 group-hover:text-gray-300 transition-colors'}`} />
                          <span className="tracking-wide">{item.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </nav>
        </aside>

        {/* Main Panel */}
        <main className="flex-1 overflow-y-auto bg-transparent relative z-10 custom-scrollbar rounded-2xl md:border border-white/5 md:bg-[rgba(14,14,16,0.2)] md:backdrop-blur-sm md:shadow-[inset_0_0_20px_rgba(0,0,0,0.5)]">
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
