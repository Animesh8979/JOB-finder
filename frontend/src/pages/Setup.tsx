/* eslint-disable @typescript-eslint/no-explicit-any */
import { Profile } from '../types';
import React, { useState, useEffect } from 'react';
import { Upload, Key, User, FileText, CheckCircle, AlertCircle, RefreshCw, Edit3 } from 'lucide-react';
import { motion } from 'framer-motion';
import type { Variants } from 'framer-motion';
import ResumeEditor from '../components/ResumeEditor';
import RecruiterScoreCard from '../components/RecruiterScoreCard';
import { useAppStore } from '../store/useAppStore';
import { apiFetch } from '../utils/api';

// Cinematic animation variants
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

interface SetupProps {
  onStatusChange: () => void;
}

export default function Setup({ onStatusChange }: SetupProps) {
  const { profile, prefs, secrets, fetchProfile, fetchPrefs, updateProfile, updatePrefs } = useAppStore();
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!profile) fetchProfile();
    if (!prefs) fetchPrefs();
  }, []);

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setMessage({ text: 'Parsing resume with AI... Please wait.', type: 'info' });
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const r = await apiFetch('/api/profile/upload', {
        method: 'POST',
        body: formData,
        showToastOnError: false
      });
      const data = await r.json();
      updateProfile(data.profile);
      setMessage({ text: 'Resume uploaded and parsed successfully!', type: 'success' });
      fetchPrefs(); // Reload identity preferences populated from resume
      onStatusChange();
    } catch (err: any) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ text: 'Saving settings...', type: 'info' });

    try {
      await apiFetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prefs, secrets }),
        showToastOnError: false
      });
      setMessage({ text: 'Settings saved successfully!', type: 'success' });
      onStatusChange();
      fetchPrefs();
    } catch (err: any) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleIdentityChange = (key: string, value: string) => {
    updatePrefs(
      { ...prefs, identity: { ...prefs.identity, [key]: value } },
      secrets
    );
  };

  const handlePrefChange = (key: string, value: unknown) => {
    updatePrefs(
      { ...prefs, [key]: value },
      secrets
    );
  };

  const handleSecretChange = (key: string, value: string) => {
    updatePrefs(
      prefs,
      { ...secrets, [key]: value }
    );
  };

  const handleSaveProfile = async (updatedProfile: Profile) => {
    try {
      await apiFetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedProfile),
        showToastOnError: false
      });
      updateProfile(updatedProfile);
      setIsEditorOpen(false);
      setMessage({ text: 'Profile updated successfully!', type: 'success' });
      onStatusChange();
    } catch (err: any) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' });
    }
  };

  return (
    <motion.div 
      variants={containerVariants} 
      initial="hidden" 
      animate="show" 
      className="space-y-8 max-w-6xl mx-auto pb-12"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Home & Setup</h1>
          <p className="text-gray-400 mt-1">Configure your AI models, keys, and candidate profile context.</p>
        </div>
      </motion.div>

      {message.text && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }} 
          animate={{ opacity: 1, scale: 1 }} 
          className={`p-4 rounded-xl flex items-center gap-3 backdrop-blur-md border ${
          message.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' :
          message.type === 'error' ? 'bg-rose-500/10 border-rose-500/30 text-rose-300' :
          'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
        }`}>
          {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
          <span className="text-sm font-medium">{message.text}</span>
        </motion.div>
      )}

      {/* Recruiter Score — inspired by interviewstreet/hiring-agent. Loaded
          once via Zustand; rule-based, zero LLM cost.
          Hidden until a resume is parsed so the score is meaningful. */}
      {profile && (
        <motion.div variants={itemVariants}>
          <RecruiterScoreCard hero />
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column: Resume upload & parsed view */}
        <motion.div variants={itemVariants} className="lg:col-span-1 space-y-6">
          <div className="surface-panel p-6 space-y-4">
            <h2 className="text-lg font-semibold text-[#0df] flex items-center gap-2">
              <FileText size={20} />
              Resume Parser
            </h2>
            <p className="text-sm text-gray-400">
              Upload your PDF, Word, or text resume. The AI will extract your skills, history, and education.
            </p>

            <label className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-8 cursor-pointer transition-all ${
              loading ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-white/20 hover:border-white/40 bg-white/0 hover:bg-white/5'
            }`}>
              {loading ? (
                <div className="flex flex-col items-center gap-2">
                  <RefreshCw className="animate-spin text-indigo-400" size={32} />
                  <span className="text-sm text-indigo-300 font-medium">Processing...</span>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 text-center">
                  <Upload className="text-gray-400 mb-1" size={32} />
                  <span className="text-sm text-gray-300 font-medium">Select Resume File</span>
                  <span className="text-xs text-gray-500">PDF, DOCX, or TXT</span>
                </div>
              )}
              <input type="file" accept=".pdf,.docx,.txt" onChange={handleResumeUpload} disabled={loading} className="hidden" />
            </label>

            {profile && profile.name && (
              <div className="mt-4 pt-4 border-t border-white/5 space-y-2">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Current Candidate:</span>
                  <span className="text-indigo-300 font-semibold">{profile.name}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Skills Extracted:</span>
                  <span className="text-gray-200">{profile.skills?.length || 0} skills</span>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Experience:</span>
                  <span className="text-gray-200">{profile.years_experience || 0} years</span>
                </div>
                <div className="mt-4 pt-4 border-t border-white/5">
                  <button 
                    onClick={() => setIsEditorOpen(true)}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 rounded-xl text-sm font-medium transition-colors border border-indigo-500/20"
                  >
                    <Edit3 size={16} />
                    Edit Parsed Resume
                  </button>
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Middle and Right: Identity, API Keys & Settings Form */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          {prefs && (
            <form onSubmit={handleSaveSettings} className="space-y-6">
              {/* Identity Preferences */}
              <div className="surface-panel p-6 space-y-4">
                <h2 className="text-lg font-semibold text-[#0df] flex items-center gap-2">
                  <User size={20} />
                  Personal Information
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Full Name</label>
                    <input type="text" value={prefs.identity.full_name} onChange={(e) => handleIdentityChange('full_name', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder="John Doe" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Email Address</label>
                    <input type="email" value={prefs.identity.email} onChange={(e) => handleIdentityChange('email', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder="john@example.com" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Phone</label>
                    <input type="text" value={prefs.identity.phone} onChange={(e) => handleIdentityChange('phone', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder="+1-555-0199" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Location</label>
                    <input type="text" value={prefs.identity.location} onChange={(e) => handleIdentityChange('location', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder="Remote, India" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">LinkedIn Profile URL</label>
                    <input type="text" value={prefs.identity.linkedin} onChange={(e) => handleIdentityChange('linkedin', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder="https://linkedin.com/in/johndoe" />
                  </div>
                </div>
              </div>

              {/* API Secrets */}
              <div className="surface-panel p-6 space-y-4">
                <h2 className="text-lg font-semibold text-[#0df] flex items-center gap-2">
                  <Key size={20} />
                  API Keys & Credentials
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Anthropic API Key</label>
                    <input type="password" value={secrets.anthropic_api_key} onChange={(e) => handleSecretChange('anthropic_api_key', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder={secrets.anthropic_api_key ? '••••••••' : 'sk-ant-...'} />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Gemini API Key</label>
                    <input type="password" value={secrets.gemini_api_key} onChange={(e) => handleSecretChange('gemini_api_key', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder={secrets.gemini_api_key ? '••••••••' : 'AIzaSy...'} />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Nvidia NIM API Key</label>
                    <input type="password" value={secrets.nvidia_api_key} onChange={(e) => handleSecretChange('nvidia_api_key', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder={secrets.nvidia_api_key ? '••••••••' : 'nvapi-...'} />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Apify API Token (Walled Garden Scrapers)</label>
                    <input type="password" value={secrets.apify_api_token} onChange={(e) => handleSecretChange('apify_api_token', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder={secrets.apify_api_token ? '••••••••' : 'apify_api_...'} />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Proxycurl API Key (Lead Gen/Networking)</label>
                    <input type="password" value={secrets.proxycurl_api_key} onChange={(e) => handleSecretChange('proxycurl_api_key', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder={secrets.proxycurl_api_key ? '••••••••' : 'Bearer...'} />
                  </div>
                </div>
              </div>

              {/* Models and Preferences */}
              <div className="surface-panel p-6 space-y-4">
                <h2 className="text-lg font-semibold text-[#0df] flex items-center gap-2">
                  <SettingsIcon size={20} />
                  AI Preferences
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">LLM Provider</label>
                    <select value={prefs.provider} onChange={(e) => handlePrefChange('provider', e.target.value)}
                      className="w-full bg-neutral-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all">
                      <option value="ollama">Ollama (Free - Local)</option>
                      <option value="claude">Anthropic (Claude)</option>
                      <option value="gemini">Google (Gemini)</option>
                      <option value="nvidia">Nvidia NIM</option>
                    </select>
                  </div>
                  {prefs.provider === 'nvidia' && (
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Nvidia Model</label>
                      <input type="text" value={prefs.nvidia_model || 'meta/llama-3.1-70b-instruct'} onChange={(e) => handlePrefChange('nvidia_model', e.target.value)}
                        className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" />
                    </div>
                  )}
                  {prefs.provider === 'ollama' && (
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Ollama Model (free, local)</label>
                      <input type="text" value={prefs.ollama_model || 'llama3.1:8b'} onChange={(e) => handlePrefChange('ollama_model', e.target.value)}
                        className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" placeholder="llama3.1:8b / qwen2.5:7b / gemma3:4b / phi3:mini" />
                    </div>
                  )}
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Writing Model</label>
                    <input type="text" value={prefs.writing_model} onChange={(e) => handlePrefChange('writing_model', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Scoring Model</label>
                    <input type="text" value={prefs.scoring_model} onChange={(e) => handlePrefChange('scoring_model', e.target.value)}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Daily Outreach Cap</label>
                    <input type="number" value={prefs.outreach_daily_cap} onChange={(e) => handlePrefChange('outreach_daily_cap', parseInt(e.target.value))}
                      className="w-full surface-panel rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 text-sm transition-all" />
                  </div>
                </div>
              </div>

              {/* Submit */}
              <button type="submit" disabled={saving}
                className="w-full md:w-auto btn-primary font-semibold rounded-xl px-8 py-4 text-sm transition-all shadow-lg shadow-indigo-500/20 active:scale-95 disabled:opacity-50">
                {saving ? 'Saving...' : 'Save All Configuration'}
              </button>
            </form>
          )}
        </motion.div>
      </div>

      {isEditorOpen && profile && (
        <ResumeEditor 
          profile={profile} 
          onSave={handleSaveProfile} 
          onClose={() => setIsEditorOpen(false)} 
        />
      )}
    </motion.div>
  );
}

// Simple local settings icon wrapper to prevent import collision
function SettingsIcon(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={props.size || 24} height={props.size || 24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}
