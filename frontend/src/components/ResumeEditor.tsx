/* eslint-disable @typescript-eslint/no-explicit-any */
import { Profile } from '../types';
import React, { useState } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ResumeEditorProps {
  profile: Profile;
  onSave: (updatedProfile: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  onClose: () => void;
}

export default function ResumeEditor({ profile, onSave, onClose }: ResumeEditorProps) {
  const [formData, setFormData] = useState<Profile>(profile || {});

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleArrayChange = (e: React.ChangeEvent<HTMLInputElement>, fieldName: string) => {
    const arr = e.target.value.split(',').map(s => s.trim()).filter(s => s);
    setFormData({ ...formData, [fieldName]: arr });
  };

  // Dynamic Array Handlers
  const handleItemChange = (listName: string, index: number, field: string, value: string) => {
    const list = [...(formData[listName] || [])];
    if (!list[index]) list[index] = {};
    list[index][field] = value;
    setFormData({ ...formData, [listName]: list });
  };

  const addItem = (listName: string, template: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const list = [...(formData[listName] || []), template];
    setFormData({ ...formData, [listName]: list });
  };

  const removeItem = (listName: string, index: number) => {
    const list = [...(formData[listName] || [])];
    list.splice(index, 1);
    setFormData({ ...formData, [listName]: list });
  };

  const handleSave = () => {
    onSave(formData);
  };

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 overflow-y-auto"
      >
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="surface-panel w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl border border-white/10"
        >
          <div className="flex items-center justify-between p-6 border-b border-white/10 shrink-0 bg-white/5">
            <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Edit Candidate Profile</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
              <X size={24} />
            </button>
          </div>
          
          <div className="p-6 overflow-y-auto flex-1 space-y-8 bg-neutral-900/50">
            {/* Basic Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Name</label>
                <input type="text" name="name" value={formData.name || ''} onChange={handleTextChange}
                  className="w-full bg-neutral-950 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all shadow-inner" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Location</label>
                <input type="text" name="location" value={formData.location || ''} onChange={handleTextChange}
                  className="w-full bg-neutral-950 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all shadow-inner" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Headline</label>
                <input type="text" name="headline" value={formData.headline || ''} onChange={handleTextChange}
                  className="w-full bg-neutral-950 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all shadow-inner" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Summary</label>
                <textarea name="summary" value={formData.summary || ''} onChange={handleTextChange} rows={3}
                  className="w-full bg-neutral-950 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm resize-none transition-all shadow-inner" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Skills (Comma-separated)</label>
                <input type="text" value={(formData.skills || []).join(', ')} onChange={(e) => handleArrayChange(e, 'skills')}
                  className="w-full bg-neutral-950 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all shadow-inner" />
              </div>
            </div>

            {/* Dynamic Arrays */}
            <div className="space-y-6 pt-4 border-t border-white/5">
              {/* Experience */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
                    Experience
                  </h3>
                  <button onClick={() => addItem('experience', { company: '', title: '', dates: '', description: '' })}
                    className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors bg-indigo-500/10 px-3 py-1.5 rounded-lg border border-indigo-500/20">
                    <Plus size={14} /> Add Role
                  </button>
                </div>
                <motion.div layout className="space-y-4">
                  <AnimatePresence mode="popLayout">
                    {(formData.experience || []).map((exp: Record<string, string>, i: number) => (
                      <motion.div 
                        key={`exp-${i}-${exp.company || 'new'}`} 
                        layout
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                        className="p-4 bg-neutral-950/80 rounded-xl border border-white/10 relative shadow-inner overflow-hidden"
                      >
                        <button onClick={() => removeItem('experience', i)} className="absolute top-4 right-4 text-gray-500 hover:text-rose-400 transition-colors bg-rose-500/10 p-1.5 rounded-md">
                          <Trash2 size={14} />
                        </button>
                        <div className="grid grid-cols-2 gap-3 pr-10">
                          <input type="text" placeholder="Company" value={exp.company || ''} onChange={(e) => handleItemChange('experience', i, 'company', e.target.value)}
                            className="w-full bg-neutral-900 border border-white/5 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 transition-all" />
                          <input type="text" placeholder="Title" value={exp.title || ''} onChange={(e) => handleItemChange('experience', i, 'title', e.target.value)}
                            className="w-full bg-neutral-900 border border-white/5 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 transition-all" />
                          <input type="text" placeholder="Dates" value={exp.dates || ''} onChange={(e) => handleItemChange('experience', i, 'dates', e.target.value)}
                            className="col-span-2 w-full bg-neutral-900 border border-white/5 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 transition-all" />
                          <textarea placeholder="Description" value={exp.description || ''} onChange={(e) => handleItemChange('experience', i, 'description', e.target.value)} rows={2}
                            className="col-span-2 w-full bg-neutral-900 border border-white/5 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 resize-none transition-all" />
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </motion.div>
              </div>

              {/* Education */}
              <div className="pt-4 border-t border-white/5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                    Education
                  </h3>
                  <button onClick={() => addItem('education', { institution: '', degree: '', dates: '' })}
                    className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 transition-colors bg-purple-500/10 px-3 py-1.5 rounded-lg border border-purple-500/20">
                    <Plus size={14} /> Add Degree
                  </button>
                </div>
                <motion.div layout className="space-y-4">
                  <AnimatePresence mode="popLayout">
                    {(formData.education || []).map((edu: Record<string, string>, i: number) => (
                      <motion.div 
                        key={`edu-${i}-${edu.institution || 'new'}`} 
                        layout
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20, transition: { duration: 0.2 } }}
                        className="grid grid-cols-[1fr_1fr_1fr_auto] gap-3 items-center bg-neutral-950/80 p-3 rounded-xl border border-white/10"
                      >
                        <input type="text" placeholder="Institution" value={edu.institution || ''} onChange={(e) => handleItemChange('education', i, 'institution', e.target.value)}
                          className="w-full bg-neutral-900 border border-white/5 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-500 transition-all" />
                        <input type="text" placeholder="Degree" value={edu.degree || ''} onChange={(e) => handleItemChange('education', i, 'degree', e.target.value)}
                          className="w-full bg-neutral-900 border border-white/5 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-500 transition-all" />
                        <input type="text" placeholder="Dates" value={edu.dates || ''} onChange={(e) => handleItemChange('education', i, 'dates', e.target.value)}
                          className="w-full bg-neutral-900 border border-white/5 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-500 transition-all" />
                        <button onClick={() => removeItem('education', i)} className="text-gray-500 hover:text-rose-400 transition-colors p-2 bg-rose-500/5 rounded-lg">
                          <Trash2 size={16} />
                        </button>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </motion.div>
              </div>
            </div>
          </div>
          
          <div className="p-6 border-t border-white/10 flex justify-end gap-3 shrink-0 bg-neutral-950/50">
            <button onClick={onClose} className="px-6 py-2 rounded-xl text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 transition-colors">
              Cancel
            </button>
            <button onClick={handleSave} className="flex items-center gap-2 px-6 py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-400 hover:to-purple-400 text-white transition-all shadow-lg shadow-indigo-500/25">
              <Save size={18} />
              Save Configuration
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
