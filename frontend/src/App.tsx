import React, { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { useAppStore } from './store/useAppStore';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import CinematicBackground from './components/CinematicBackground';
import CommandCenter from './pages/CommandCenter';

const queryClient = new QueryClient();

function AppContent() {
  useEffect(() => {
    // Initial fetch to get status immediately without waiting for SSE
    axios.get('/api/status').then(res => {
      useAppStore.setState({ readiness: res.data });
    }).catch(console.error);

    const sse = new EventSource('/api/stream/events');
    sse.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.readiness) {
          useAppStore.setState({ readiness: data.readiness });
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };
    sse.onerror = (err) => {
      console.warn("SSE connection error, it will auto-reconnect", err);
    };

    return () => sse.close();
  }, []);

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

      <div className="w-full h-screen p-0 md:p-3 z-10 flex">
        <main className="flex-1 overflow-y-auto bg-transparent relative custom-scrollbar rounded-2xl md:border border-white/[0.04] md:bg-[rgba(10,10,12,0.15)] md:backdrop-blur-sm md:shadow-[inset_0_0_24px_rgba(0,0,0,0.4)]">
          <CommandCenter />
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
