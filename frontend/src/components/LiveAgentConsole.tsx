import React, { useEffect, useRef } from 'react';
import { Terminal, Activity, Server, Zap } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export default function LiveAgentConsole() {
  const logs = useAppStore((s) => s.terminalLogs);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="h-48 w-full bg-[#0a0a0a]/95 backdrop-blur-xl border-t border-indigo-500/30 overflow-hidden flex flex-col font-mono text-[11px] text-indigo-300/80 shadow-[0_-10px_40px_rgba(79,70,229,0.15)] shrink-0 relative z-50">
      {/* Header */}
      <div className="flex justify-between items-center px-4 py-1.5 bg-indigo-950/40 border-b border-indigo-500/20">
        <div className="flex items-center gap-2 text-indigo-300 font-bold uppercase tracking-widest text-[10px]">
          <Terminal size={12} className="text-indigo-400" />
          Antigravity OS Terminal
          <span className="flex h-2 w-2 relative ml-1">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-indigo-500 top-[1px] left-[1px]"></span>
          </span>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-indigo-500/70">
          <span className="flex items-center gap-1"><Server size={10} /> 127.0.0.1</span>
          <span className="flex items-center gap-1"><Zap size={10} /> 12ms ping</span>
          <span className="flex items-center gap-1"><Activity size={10} /> ACTIVE</span>
        </div>
      </div>
      
      {/* Scanline overlay */}
      <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.03),rgba(0,255,0,0.01),rgba(0,0,255,0.03))] bg-[length:100%_4px,3px_100%] z-10 opacity-40 mix-blend-overlay"></div>

      {/* Logs */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-0.5 relative z-20 custom-scrollbar">
        {logs.map((l) => (
          <div key={l.id} className="flex gap-3 hover:bg-indigo-900/20 px-1.5 py-0.5 rounded transition-colors break-all">
            <span className="text-indigo-500/50 shrink-0 select-none">
              {new Date(l.time).toLocaleTimeString('en-US', { hour12: false, fractionalSecondDigits: 3 })}
            </span>
            <span className={
              l.type === 'error' ? 'text-rose-400 font-bold' : 
              l.type === 'success' ? 'text-emerald-300 font-bold' : 
              'text-indigo-300'
            }>
              {l.msg}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
