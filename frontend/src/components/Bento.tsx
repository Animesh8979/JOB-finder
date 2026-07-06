/**
 * Bento — world-class asymmetric grid primitive used on the Dashboard's hero.
 * Slot layout: a span-2 / span-1 / span-2 etc grid; comes with built-in
 * reveal-on-mount motion + gradient borders.
 */
import React from 'react';
import { motion } from 'framer-motion';
import SpotlightCard from './SpotlightCard';

export interface BentoSlot {
  /** Grid-row span (1-3) */
  spanY?: number;
  /** Grid-col span (1-4) */
  spanX?: number;
  /** Custom showcase: gradient class pair */
  accent?: 'indigo' | 'emerald' | 'amber' | 'rose' | 'sky' | 'violet';
}

interface BentoProps {
  slots: Array<{ key: string; el: React.ReactNode; spanX?: number; spanY?: number; accent?: string }>;
}

const ACCENT_MAP: Record<string, string> = {
  indigo: 'from-indigo-500/15 to-blue-500/15',
  emerald: 'from-emerald-500/15 to-teal-500/15',
  amber: 'from-amber-500/15 to-orange-500/15',
  rose: 'from-rose-500/15 to-pink-500/15',
  sky: 'from-sky-500/15 to-cyan-500/15',
  violet: 'from-violet-500/15 to-fuchsia-500/15',
};

export default function Bento({ slots }: BentoProps) {
  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.09, delayChildren: 0.1 } },
  };
  const item = {
    hidden: { opacity: 0, y: 16, filter: 'blur(6px)' },
    show: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { type: 'spring' as const, stiffness: 220, damping: 24 } },
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 md:grid-cols-4 gap-3 md:gap-4"
    >
      {slots.map((s) => {
        const cls = s.accent && ACCENT_MAP[s.accent] ? ACCENT_MAP[s.accent] : 'from-white/5 to-white/0';
        const col = `md:col-span-${Math.min(4, Math.max(1, s.spanX ?? 1))}`;
        const row = `md:row-span-${Math.min(3, Math.max(1, s.spanY ?? 1))}`;
        return (
          <motion.div key={s.key} variants={item} className={`${col} ${row} min-h-[140px]`}>
            <SpotlightCard className={`h-full bg-gradient-to-br ${cls}`} innerClassName="p-5 h-full">
              {s.el}
            </SpotlightCard>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
