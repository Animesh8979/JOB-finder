/**
 * SpotlightCard — premium card that follows the cursor with a local light effect.
 * Used as the standard "card" primitive everywhere in the app.
 *
 * - Cursor position drives a CSS conic-gradient "spotlight"
 * - Inset border subtly lights up when mouse enters
 * - Magnetic lift on hover
 *
 * Performance: pointer-position is captured passively; the radial-gradient is
 * set via CSS variables so the browser handles the paint cheaply.
 */
import React, { useRef, useCallback, MouseEvent } from 'react';

interface SpotlightCardProps {
  children: React.ReactNode;
  className?: string;
  innerClassName?: string;
  spotlightColor?: string;
  intensity?: number;
  onClick?: () => void;
}

export default function SpotlightCard({
  children,
  className = '',
  innerClassName = '',
  spotlightColor = 'rgba(129, 140, 248, 0.18)',
  intensity = 1,
  onClick,
}: SpotlightCardProps) {
  const ref = useRef<HTMLDivElement>(null);

  const onMove = useCallback((e: MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', `${e.clientX - r.left}px`);
    el.style.setProperty('--my', `${e.clientY - r.top}px`);
    el.style.setProperty('--spot-color', spotlightColor);
    el.style.setProperty('--spot-alpha', String(intensity));
  }, [spotlightColor, intensity]);

  const onLeave = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty('--mx', `-9999px`);
    el.style.setProperty('--my', `-9999px`);
  }, []);

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      onClick={onClick}
      className={`spotlight-card ${className}`}
      style={{ position: 'relative', overflow: 'hidden' }}
    >
      <div className={`spotlight-card-inner ${innerClassName}`}>{children}</div>
    </div>
  );
}
