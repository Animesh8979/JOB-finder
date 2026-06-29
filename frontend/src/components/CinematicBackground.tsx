import React from 'react';

/**
 * CinematicBackground — Vercel-style layered radial-gradient aurora.
 * 
 * Technique: All gradients are on a SINGLE element's background-image.
 * No child elements, no z-index conflicts, no blend-mode-against-black bug.
 * Uses background-blend-mode: screen between layers within the SAME element.
 */
export default function CinematicBackground() {
  return (
    <div
      className="fixed inset-0 w-full h-full z-0 pointer-events-none aurora-bg"
      aria-hidden="true"
    >
      {/* Grid overlay (Vercel-style 24px grid) */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px)
          `,
          backgroundSize: '24px 24px',
          maskImage: 'linear-gradient(to bottom, white 0%, transparent 70%)',
          WebkitMaskImage: 'linear-gradient(to bottom, white 0%, transparent 70%)',
        }}
      />

      {/* Noise/grain overlay (anti-banding) */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.045]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
        }}
      />

      {/* Subtle bottom vignette for text readability — LIGHT, not 80% */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'linear-gradient(to top, rgba(9,9,11,0.5) 0%, transparent 40%)',
        }}
      />
    </div>
  );
}
