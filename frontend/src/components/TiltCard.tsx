import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';

interface TiltCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export default function TiltCard({ children, className = '', onClick }: TiltCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const [glareX, setGlareX] = useState(50);
  const [glareY, setGlareY] = useState(50);
  const [glareOpacity, setGlareOpacity] = useState(0);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Calculate rotation (-10 to +10 degrees for subtlety)
    const multiplier = 10;
    const rX = ((y / rect.height) - 0.5) * -multiplier;
    const rY = ((x / rect.width) - 0.5) * multiplier;
    
    setRotateX(rX);
    setRotateY(rY);

    // Calculate glare position
    setGlareX((x / rect.width) * 100);
    setGlareY((y / rect.height) * 100);
    setGlareOpacity(1); // Full opacity handled by gradient alpha
  };

  const handleMouseLeave = () => {
    setRotateX(0);
    setRotateY(0);
    setGlareOpacity(0);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{ perspective: 1200 }}
      className={`relative ${onClick ? 'cursor-pointer' : ''}`}
    >
      <motion.div
        animate={{
          rotateX,
          rotateY,
          transformPerspective: 1200,
        }}
        transition={{ type: 'spring', stiffness: 200, damping: 25, mass: 0.5 }}
        className={`w-full h-full relative overflow-hidden rounded-[inherit] ${className}`}
        style={{
          transformStyle: "preserve-3d"
        }}
      >
        {/* Dynamic Studio Glare Overlay */}
        <motion.div 
          className="absolute inset-0 pointer-events-none z-50 mix-blend-color-dodge transition-opacity duration-300"
          animate={{ opacity: glareOpacity }}
          style={{
            background: `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,0.15) 0%, rgba(0,243,255,0.05) 30%, transparent 60%)`
          }}
        />
        {/* Edge Reflection */}
        <motion.div 
          className="absolute inset-0 pointer-events-none z-40 transition-opacity duration-300"
          animate={{ opacity: glareOpacity * 0.5 }}
          style={{
            background: `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,0.1) 0%, transparent 80%)`
          }}
        />
        {children}
      </motion.div>
    </motion.div>
  );
}
