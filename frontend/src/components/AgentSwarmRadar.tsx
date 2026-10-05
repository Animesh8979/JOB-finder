import React, { useEffect, useRef } from 'react';

export default function AgentSwarmRadar() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = canvas.width;
    let height = canvas.height;

    const resize = () => {
      width = canvas.width = canvas.parentElement?.clientWidth || 300;
      height = canvas.height = 300;
    };
    resize();
    window.addEventListener('resize', resize);

    // Generate random nodes
    const nodes = Array.from({ length: 40 }).map(() => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: Math.random() * 2 + 1,
      baseAlpha: Math.random() * 0.5 + 0.1,
    }));

    let angle = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      
      // Radar center
      const cx = width / 2;
      const cy = height / 2;
      const radarRadius = Math.min(cx, cy) - 20;

      // Draw grid rings
      ctx.strokeStyle = 'rgba(79, 70, 229, 0.15)'; // Indigo
      ctx.lineWidth = 1;
      for (let i = 1; i <= 3; i++) {
        ctx.beginPath();
        ctx.arc(cx, cy, (radarRadius / 3) * i, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Draw crosshairs
      ctx.beginPath();
      ctx.moveTo(cx, cy - radarRadius);
      ctx.lineTo(cx, cy + radarRadius);
      ctx.moveTo(cx - radarRadius, cy);
      ctx.lineTo(cx + radarRadius, cy);
      ctx.stroke();

      // Radar sweep
      angle += 0.03;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, radarRadius, angle, angle + 0.2);
      ctx.lineTo(cx, cy);
      ctx.fillStyle = 'rgba(79, 70, 229, 0.2)';
      ctx.fill();

      // Draw and update nodes
      ctx.fillStyle = '#818cf8'; // text-indigo-400
      nodes.forEach(node => {
        // Move
        node.x += node.vx;
        node.y += node.vy;
        
        // Bounce
        if (node.x < 0 || node.x > width) node.vx *= -1;
        if (node.y < 0 || node.y > height) node.vy *= -1;

        // Check if node is hit by radar sweep
        const dx = node.x - cx;
        const dy = node.y - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        let nodeAngle = Math.atan2(dy, dx);
        if (nodeAngle < 0) nodeAngle += Math.PI * 2;
        
        const normalizedRadarAngle = angle % (Math.PI * 2);

        // Simple angle diff
        let diff = Math.abs(normalizedRadarAngle - nodeAngle);
        if (diff > Math.PI) diff = Math.PI * 2 - diff;

        let isHit = false;
        if (dist < radarRadius && diff < 0.25) {
          isHit = true;
        }

        // Draw connections to nearby nodes
        nodes.forEach(other => {
          const odx = other.x - node.x;
          const ody = other.y - node.y;
          const odist = Math.sqrt(odx * odx + ody * ody);
          if (odist < 50) {
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(other.x, other.y);
            ctx.strokeStyle = `rgba(79, 70, 229, ${0.15 * (1 - odist / 50)})`;
            ctx.stroke();
          }
        });

        // Draw node
        ctx.beginPath();
        ctx.arc(node.x, node.y, isHit ? node.radius * 2 : node.radius, 0, Math.PI * 2);
        ctx.fillStyle = isHit ? 'rgba(52, 211, 153, 0.9)' : `rgba(79, 70, 229, ${node.baseAlpha})`;
        ctx.fill();
        
        // Glow if hit
        if (isHit) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius * 4, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(52, 211, 153, 0.2)';
          ctx.fill();
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <div className="w-full h-full bg-black/40 border border-indigo-500/20 rounded-2xl relative overflow-hidden flex flex-col items-center justify-center">
      <div className="absolute top-4 left-4 z-10">
        <h3 className="text-xs font-bold text-indigo-300 font-mono tracking-widest uppercase flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Swarm Link Active
        </h3>
        <p className="text-[9px] text-zinc-500 font-mono mt-1">
          Scraping topology & network density
        </p>
      </div>
      <canvas ref={canvasRef} className="w-full h-[300px]" style={{ filter: 'drop-shadow(0 0 10px rgba(79,70,229,0.2))' }} />
    </div>
  );
}
