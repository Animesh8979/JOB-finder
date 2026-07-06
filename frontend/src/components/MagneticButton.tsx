/**
 * MagneticButton — a button that subtly "pulls" toward the cursor when nearby.
 * Used for the most important CTAs on every page to add tactility.
 *
 * Physics: spring-damped translation; never moves more than ~6px so it never
 * occludes other UI. Disabled buttons skip the effect entirely.
 */
import React, { useRef, useState, MouseEvent } from 'react';
import { motion } from 'framer-motion';

interface MagneticButtonProps {
  children: React.ReactNode;
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  className?: string;
  strength?: number;     // 1..8
  title?: string;
  type?: 'button' | 'submit' | 'reset';
  ariaLabel?: string;
}

export default function MagneticButton({
  children,
  onClick,
  disabled = false,
  className = '',
  strength = 4,
  title,
  type = 'button',
  ariaLabel,
}: MagneticButtonProps) {
  const ref = useRef<HTMLButtonElement>(null);
  const [{ dx, dy }, set] = useState({ dx: 0, dy: 0 });

  const onMove = (e: MouseEvent<HTMLButtonElement>) => {
    if (disabled) return;
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const relX = e.clientX - (r.left + r.width / 2);
    const relY = e.clientY - (r.top + r.height / 2);
    set({ dx: (relX / r.width) * strength, dy: (relY / r.height) * strength });
  };

  const onLeave = () => set({ dx: 0, dy: 0 });

  return (
    <motion.button
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      onClick={onClick}
      disabled={disabled}
      className={className}
      title={title}
      type={type}
      aria-label={ariaLabel}
      animate={{ x: dx, y: dy }}
      transition={{ type: 'spring', stiffness: 220, damping: 16, mass: 0.4 }}
      whileTap={!disabled ? { scale: 0.97 } : undefined}
    >
      {children}
    </motion.button>
  );
}
