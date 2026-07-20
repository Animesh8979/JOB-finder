import React from 'react';
import { X } from 'lucide-react';
import Setup from '../pages/Setup';

interface SettingsDrawerProps {
  onClose: () => void;
  onStatusChange: () => void;
}

export default function SettingsDrawer({ onClose, onStatusChange }: SettingsDrawerProps) {
  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end animate-in fade-in duration-200">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Content */}
      <div className="relative w-full max-w-5xl bg-[#0e0e12] border-l border-white/10 h-full flex flex-col shadow-2xl z-10 overflow-hidden">
        
        {/* Drawer Header */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between bg-white/[0.01]">
          <h2 className="text-xl font-bold text-white">Profile & Settings</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Setup Page Content */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          <Setup onStatusChange={onStatusChange} />
        </div>
      </div>
    </div>
  );
}
