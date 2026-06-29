/* eslint-disable @typescript-eslint/no-explicit-any */
export interface Job {
  id: number;
  title?: string;
  company?: string;
  location?: string;
  url?: string;
  apply_url?: string;
  match_score?: number;
  match_reason?: string;
  created_at: string;
  fit_analysis?: string;
  red_flags?: string;
}

export interface Application {
  id: number;
  job_id: number;
  status?: string;
  company?: string;
  title?: string;
  tailored_resume_path?: string;
  tailored_resume_text?: string;
  cover_letter_path?: string;
  cover_letter_text?: string;
  notes?: string;
  applied_at?: string;
  updated_at?: string;
  created_at?: string;
  match_score?: number;
}

export interface Profile {
  name?: string;
  email?: string;
  skills?: string[];
  years_experience?: number;
  [key: string]: unknown;
}

export interface Preferences {
  provider?: string;
  nvidia_model?: string;
  writing_model?: string;
  scoring_model?: string;
  outreach_daily_cap?: number;
  identity: {
    full_name?: string;
    email?: string;
    phone?: string;
    location?: string;
    linkedin?: string;
  };
}

export interface Secrets {
  anthropic_api_key?: string;
  gemini_api_key?: string;
  nvidia_api_key?: string;
  apify_api_token?: string;
  proxycurl_api_key?: string;
}

export interface Contact {
  id: number;
  name: string;
  email: string;
  company?: string;
  role?: string;
  notes?: string;
  source?: string;
  job_id?: number;
  title?: string;
  created_at?: string;
  subject?: string;
  contact_name?: string;
  contact_email?: string;
  body?: string;
}

export interface OutreachLog {
  id: number;
  contact_name?: string;
  contact_email?: string;
  subject?: string;
  body?: string;
  created_at?: string;
}
