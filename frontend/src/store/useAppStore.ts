import type { Profile, Preferences, Secrets, RecruiterScoreReport } from '../types';
import { create } from 'zustand';
import { apiFetch } from '../utils/api';

interface RecruiterScoreState {
  loading: boolean;
  loaded: boolean;
  error?: string;
  data?: RecruiterScoreReport;
}

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
  recruiterScore: RecruiterScoreState;
  
  checkReadiness: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  fetchPrefs: () => Promise<void>;
  fetchRecruiterScore: () => Promise<void>;
  updateProfile: (profile: Profile) => void;
  updatePrefs: (prefs: Preferences, secrets?: Secrets) => void;
  setRecruiterScore: (state: Partial<RecruiterScoreState>) => void;
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
  recruiterScore: { loading: false, loaded: false },

    checkReadiness: async () => {
    // Skip if page is not visible
    if (document.hidden) return;
    
    try {
      const response = await apiFetch('/api/status', { showToastOnError: false });
      const data = await response.json();
      set({ readiness: data });
    } catch (e) {
      console.error('Failed to fetch readiness status:', e);
    }
  },

  fetchProfile: async () => {
    try {
      const response = await apiFetch('/api/profile', { showToastOnError: false });
      const data = await response.json();
      set({ profile: data });
    } catch (e) {
      console.error('Failed to fetch profile:', e);
    }
  },

  fetchPrefs: async () => {
    try {
      const response = await apiFetch('/api/preferences', { showToastOnError: false });
      const data = await response.json();
      set({ prefs: data.prefs, secrets: data.secrets });
    } catch (e) {
      console.error('Failed to fetch preferences:', e);
    }
  },

  updateProfile: (profile) => set({ profile, recruiterScore: { loading: false, loaded: false } }),
  updatePrefs: (prefs, secrets) => set({ prefs, secrets }),

  fetchRecruiterScore: async () => {
    set((s) => ({ recruiterScore: { ...s.recruiterScore, loading: true, error: undefined } }));
    try {
      const response = await apiFetch('/api/recruiter_score', { showToastOnError: false });
      const data: RecruiterScoreReport = await response.json();
      set({ recruiterScore: { loading: false, loaded: true, data } });
    } catch (e) {
      set((s) => ({
        recruiterScore: { ...s.recruiterScore, loading: false, loaded: true, error: e instanceof Error ? e.message : String(e) },
      }));
    }
  },

  setRecruiterScore: (state) => set((s) => ({ recruiterScore: { ...s.recruiterScore, ...state } }))
}));
