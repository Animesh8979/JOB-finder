/**
 * TypeRotator — premium rotating status text with caret blink. Used in
 * page headers and Hero greetings for cinematic flair.
 */
import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface TypeRotatorProps {
  items: string[];
  interval?: number;
  className?: string;
}

export default function TypeRotator({ items, interval = 2800, className = '' }: TypeRotatorProps) {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (items.length < 2) return;
    const t = setInterval(() => setI((p) => (p + 1) % items.length), interval);
    return () => clearInterval(t);
  }, [items.length, interval]);

  if (items.length === 0) return null;
  const current = items[i];

  return (
    <span className={`inline-flex items-baseline ${className}`}>
      <AnimatePresence mode="wait">
        <motion.span
          key={i}
          initial={{ y: 12, opacity: 0, filter: 'blur(4px)' }}
          animate={{ y: 0, opacity: 1, filter: 'blur(0px)' }}
          exit={{ y: -12, opacity: 0, filter: 'blur(4px)' }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        >
          {current}
        </motion.span>
      </AnimatePresence>
      <span className="ml-0.5 inline-block w-[2px] h-[1em] bg-current align-middle ml-0.5 caret-blink" />
    </span>
  );
}
