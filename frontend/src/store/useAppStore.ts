import type { Profile, Preferences, Secrets } from '../types';
import { create } from 'zustand';
import { apiFetch } from '../utils/api';

interface AppState {
  readiness: {
    ai_key: boolean;
    resume: boolean;
    identity: boolean;
  };
  profile: Profile | null;
  prefs: Preferences | null;
  secrets: Secrets | null;
  isLoading: boolean;
  
  checkReadiness: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  fetchPrefs: () => Promise<void>;
  updateProfile: (profile: Profile) => void;
  updatePrefs: (prefs: Preferences, secrets?: Secrets) => void;
}

export const useAppStore = create<AppState>((set) => ({
  readiness: { ai_key: false, resume: false, identity: false },
  profile: null,
  prefs: null,
  secrets: {
    anthropic_api_key: '',
    gemini_api_key: '',
    nvidia_api_key: '',
    apify_api_token: '',
    proxycurl_api_key: ''
  },
  isLoading: false,

  checkReadiness: async () => {
    // Skip if page is not visible
    if (document.hidden) return;
    
    try {
      const response = await apiFetch('/api/status', { showToastOnError: false });
      const data = await response.json();
      set({ readiness: data });
    } catch (e: any) {
      console.error('Failed to fetch readiness status:', e);
    }
  },

  fetchProfile: async () => {
    try {
      const response = await apiFetch('/api/profile', { showToastOnError: false });
      const data = await response.json();
      set({ profile: data });
    } catch (e: any) {
      console.error('Failed to fetch profile:', e);
    }
  },

  fetchPrefs: async () => {
    try {
      const response = await apiFetch('/api/preferences', { showToastOnError: false });
      const data = await response.json();
      set({ prefs: data.prefs, secrets: data.secrets });
    } catch (e: any) {
      console.error('Failed to fetch preferences:', e);
    }
  },

  updateProfile: (profile) => set({ profile }),
  updatePrefs: (prefs, secrets) => set({ prefs, secrets })
}));
