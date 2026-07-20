import React, { useRef, useEffect } from 'react';

/**
 * CinematicBackground — World-class animated aurora mesh with:
 *  - Cursor-reactive parallax orbs (magnetic pull toward mouse)
 *  - Animated grid with perspective fade
 *  - SVG noise grain overlay
 *  - Bottom vignette for text readability
 *  - Performance: requestAnimationFrame, transform-only animations.
 */
export default function CinematicBackground() {
  const orb1Ref = useRef<HTMLDivElement>(null);
  const orb2Ref = useRef<HTMLDivElement>(null);
  const orb3Ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let rafId: number;
    let targetX = 0.5, targetY = 0.5;
    let currentX = 0.5, currentY = 0.5;

    const onMouseMove = (e: MouseEvent) => {
      targetX = e.clientX / window.innerWidth;
      targetY = e.clientY / window.innerHeight;
    };

    const tick = () => {
      // Smooth lerp toward the mouse target
      currentX += (targetX - currentX) * 0.045;
      currentY += (targetY - currentY) * 0.045;

      const dx = (currentX - 0.5) * 2; // -1..1
      const dy = (currentY - 0.5) * 2;

      if (orb1Ref.current) {
        orb1Ref.current.style.transform = `translate(${dx * 30}px, ${dy * 25}px)`;
      }
      if (orb2Ref.current) {
        orb2Ref.current.style.transform = `translate(${dx * -45}px, ${dy * -30}px)`;
      }
      if (orb3Ref.current) {
        orb3Ref.current.style.transform = `translate(${dx * 20}px, ${dy * -40}px)`;
      }

      rafId = requestAnimationFrame(tick);
    };

    window.addEventListener('mousemove', onMouseMove, { passive: true });
    rafId = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div
      className="fixed inset-0 w-full h-full z-0 pointer-events-none aurora-bg"
      aria-hidden="true"
    >
      {/* Cursor-reactive orbs */}
      <div
        ref={orb1Ref}
        className="absolute pointer-events-none will-change-transform"
        style={{
          top: '8%',
          right: '12%',
          width: '480px',
          height: '480px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 70%)',
          filter: 'blur(70px)',
          animation: 'cosmicDrift 25s ease-in-out infinite reverse',
          transition: 'transform 0.1s linear',
        }}
      />
      <div
        ref={orb2Ref}
        className="absolute pointer-events-none will-change-transform"
        style={{
          bottom: '5%',
          left: '8%',
          width: '360px',
          height: '360px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(168, 85, 247, 0.08) 0%, transparent 70%)',
          filter: 'blur(55px)',
          animation: 'cosmicDrift 30s ease-in-out infinite',
          transition: 'transform 0.1s linear',
        }}
      />
      <div
        ref={orb3Ref}
        className="absolute pointer-events-none will-change-transform"
        style={{
          top: '40%',
          left: '45%',
          width: '280px',
          height: '280px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(56, 189, 248, 0.06) 0%, transparent 70%)',
          filter: 'blur(50px)',
          animation: 'cosmicDrift 22s ease-in-out infinite',
          transition: 'transform 0.1s linear',
        }}
      />

      {/* Animated grid with perspective fade */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(99, 102, 241, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '36px 36px',
          maskImage: 'linear-gradient(to bottom, white 0%, transparent 55%)',
          WebkitMaskImage: 'linear-gradient(to bottom, white 0%, transparent 55%)',
        }}
      />

      {/* SVG noise grain */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.035]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
        }}
      />

      {/* Bottom vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'linear-gradient(to top, rgba(3,3,3,0.6) 0%, transparent 35%)',
        }}
      />
    </div>
  );
}
