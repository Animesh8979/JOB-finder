/**
 * HeroGreeting — the "bombshell" first impression on the Dashboard. Cinematic,
 * weighted, personalized. Uses TypeRotator for variant taglines and a pulsing
 * conic-ring for the "agent online" mark.
 */
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import TypeRotator from './TypeRotator';

interface HeroGreetingProps {
  candidateName?: string;
  taglineIndex?: number;
  agentOnline?: boolean;
  jobCount?: number;
  bestScoreCount?: number;
}

const TAGLINES = [
  'Your job search, on autopilot.',
  'Discover · Tailor · Apply · Track.',
  'Twenty boards. One quiet cockpit.',
  'Engineering the tedious away.',
];

export default function HeroGreeting({
  candidateName,
  agentOnline = true,
  jobCount = 0,
  bestScoreCount = 0,
}: HeroGreetingProps) {
  const [now, setNow] = useState<string>('');
  useEffect(() => {
    const update = () => {
      const d = new Date();
      setNow(
        d.toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit',
        })
      );
    };
    update();
    const t = setInterval(update, 30000);
    return () => clearInterval(t);
  }, []);

  const greetable = candidateName?.trim() || 'Operator';
  const greeting = greetingFor();

  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      className="relative overflow-hidden surface-panel p-6 md:p-8"
    >
      {/* Conic glow accent top right */}
      <div
        className="absolute -top-32 -right-32 w-[420px] h-[420px] opacity-30 pointer-events-none"
        style={{
          background:
            'radial-gradient(circle, rgba(99,102,241,0.35) 0%, rgba(168,85,247,0.15) 35%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />

      <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="min-w-0">
          <div className="text-[11px] text-zinc-500 uppercase tracking-[0.18em] font-medium flex items-center gap-2">
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full ${
                agentOnline ? 'bg-emerald-400 pulse-live' : 'bg-amber-400'
              }`}
            />
            {agentOnline ? 'Agent Online' : 'Agent Idle'}
            <span className="text-zinc-700">/</span>
            <span>{now}</span>
          </div>

          <h1 className="mt-3 text-3xl md:text-5xl font-bold tracking-tight leading-[1.05]">
            <span className="text-zinc-400 font-medium">{greeting},</span>{' '}
            <span className="text-gradient-primary">{greetable}</span>
          </h1>

          <p className="mt-3 max-w-[64ch] text-sm md:text-base text-zinc-400 leading-relaxed">
            <TypeRotator items={TAGLINES} interval={3400} />
          </p>
        </div>

        {/* Conic ring + numbers */}
        <div className="flex items-center gap-5">
          <div className="relative w-[88px] h-[88px] shrink-0">
            <div className="absolute inset-0 rounded-full conic-ring" />
            <div className="absolute inset-2 rounded-full bg-[#060606] flex items-center justify-center">
              <span className="text-base font-semibold tabnum">{jobCount}</span>
            </div>
          </div>
          <div className="text-[11px] text-zinc-500 uppercase tracking-[0.18em] font-medium leading-tight">
            Tracked
            <div className="text-zinc-100 text-2xl font-semibold mt-1 tabnum">{bestScoreCount}</div>
            <div className="text-zinc-500 mt-1">high-match</div>
          </div>
        </div>
      </div>
    </motion.section>
  );
}

function greetingFor(): string {
  const h = new Date().getHours();
  if (h < 5) return 'Up late';
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  if (h < 21) return 'Good evening';
  return 'Quiet night';
}
