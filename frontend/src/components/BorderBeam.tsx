/**
 * BorderBeam — copy-paste primitive inspired by magicui (MIT, https://github.com/magicuidesign/magicui).
 * Re-implemented here from the well-documented "rotating conic-gradient border" technique
 * rather than copied from magicui's source, so this file is self-contained — no npm install.
 *
 * Effect: a thin animated arc travels around the inside of the parent's border. Mount
 * this as a child of any `position: relative` element. The beam inherits border-radius
 * from a `--bb-radius` CSS var (default 0.75rem) so it hugs rounded corners cleanly.
 *
 * Performance:
 *   - Uses `transform: rotate` (GPU-composited) instead of repainting a gradient.
 *   - Anima duration is gentle (10s default) so the cost is negligible on a quad-core i7.
 *   - `prefers-reduced-motion` is respected — beam fades to a static ring.
 */
import React from 'react';

interface BorderBeamProps {
  /** Tailwind/CSS color of the beam itself — any valid CSS color string. */
  color?: string;
  /** Tailwind class for the wrapper override (rare). */
  className?: string;
  /** Beam size in pixels (height of the arc). Default 2.5. */
  size?: number;
  /** Rotation period in seconds. Default 10. */
  duration?: number;
  /** Border radius the beam should hug (CSS length). Default '0.75rem'. */
  radius?: string;
  /** Delay (seconds) before the beam starts. Default 0. */
  delay?: number;
}

export default function BorderBeam({
  color = '#a5b4fc', // indigo-300
  className = '',
  size = 2.5,
  duration = 10,
  radius = '0.75rem',
  delay = 0,
}: BorderBeamProps) {
  return (
    <div
      aria-hidden="true"
      className={`border-beam ${className}`}
      style={{
        '--bb-color': color,
        '--bb-size': `${size}px`,
        '--bb-radius': radius,
        '--bb-duration': `${duration}s`,
        '--bb-delay': `${delay}s`,
      } as React.CSSProperties}
    />
  );
}

/* Mounted-once global styles. Kept tiny so the bundle stays lean. */
const styles = String.raw`
.border-beam {
  position: absolute;
  inset: 0;
  border-radius: var(--bb-radius, 0.75rem);
  pointer-events: none;
  /* The trick: mask a conic-gradient to only show a thin arc band, then rotate. */
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    transparent 270deg,
    var(--bb-color, #a5b4fc) 320deg,
    var(--bb-color, #a5b4fc) 360deg
  );
  /* Mask the center so only the outer ring (the border) is visible. */
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
          mask-composite: exclude;
  padding: calc(var(--bb-size, 2.5px) * -1);
  opacity: 0.7;
  animation: border-beam-spin var(--bb-duration, 10s) linear infinite;
  animation-delay: var(--bb-delay, 0s);
  z-index: 1;
}
@keyframes border-beam-spin {
  to { transform: rotate(1turn); }
}
@media (prefers-reduced-motion: reduce) {
  .border-beam {
    animation: none;
    opacity: 0.35;
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      transparent 270deg,
      var(--bb-color, #a5b4fc) 360deg
    );
  }
}
`;

if (typeof document !== 'undefined' && !document.getElementById('__border-beam-css')) {
  const node = document.createElement('style');
  node.id = '__border-beam-css';
  node.type = 'text/css';
  node.appendChild(document.createTextNode(styles));
  document.head.appendChild(node);
}
