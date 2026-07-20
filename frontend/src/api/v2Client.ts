/* eslint-disable @typescript-eslint/no-explicit-any */
import { apiFetch } from '../utils/api';

export interface SearchIntentV2 {
  query: string;
  location?: string;
  remote_only?: boolean;
  sources?: string[];
  auto_apply?: boolean;
}

export interface JobViewV2 {
  id: number;
  title: string;
  company: string;
  location?: string | null;
  remote?: boolean;
  url?: string | null;
  apply_url?: string | null;
  description?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string | null;
  posted_at?: string | null;
  match_score?: number | null;
  match_reason?: string | null;
  status: string;
}

export interface RunViewV2 {
  run_id: string;
  kind: string;
  status: string;
  phase?: string | null;
  progress_current?: number;
  progress_total?: number;
  message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  result_json?: any;
  error_message?: string | null;
}

export interface AuditRequestV2 {
  profile?: Record<string, any>;
  prefs?: Record<string, any>;
}

export async function listJobsV2(params: { limit?: number; min_score?: number; remote_only?: boolean } = {}): Promise<JobViewV2[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.append('limit', String(params.limit));
  if (params.min_score !== undefined) query.append('min_score', String(params.min_score));
  if (params.remote_only !== undefined) query.append('remote_only', String(params.remote_only));
  
  const res = await apiFetch(`/api/v2/jobs?${query.toString()}`);
  return res.json();
}

export async function getJobV2(id: number): Promise<JobViewV2> {
  const res = await apiFetch(`/api/v2/jobs/${id}`);
  return res.json();
}

export async function triggerSearchV2(intent: { query: string; location?: string; remote_only?: boolean; sources?: string[]; auto_apply?: boolean }): Promise<RunViewV2> {
  const res = await apiFetch('/api/v2/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(intent)
  });
  return res.json();
}

export async function triggerAuditV2(id: number, req: AuditRequestV2 = {}): Promise<RunViewV2> {
  const res = await apiFetch(`/api/v2/jobs/${id}/audit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req)
  });
  return res.json();
}

export async function triggerApplyV2(id: number): Promise<RunViewV2> {
  const res = await apiFetch(`/api/v2/jobs/${id}/apply`, {
    method: 'POST'
  });
  return res.json();
}

export async function listRunsV2(params: { limit?: number; status?: string } = {}): Promise<RunViewV2[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.append('limit', String(params.limit));
  if (params.status) query.append('status', params.status);
  
  const res = await apiFetch(`/api/v2/runs?${query.toString()}`);
  return res.json();
}

export async function getRunV2(runId: string): Promise<RunViewV2> {
  const res = await apiFetch(`/api/v2/runs/${runId}`);
  return res.json();
}

/** Subscribe to realtime v2 SSE events and invoke callback when runs change. */
export function subscribeToRunsV2(
  onRunEvent: (payload: { event: string; data: any }) => void,
  runId?: string
): () => void {
  const url = runId ? `/api/v2/events?run_id=${encodeURIComponent(runId)}` : '/api/v2/events';
  const sse = new EventSource(url);

  const handleMsg = (event: MessageEvent, eventName = 'message') => {
    try {
      const data = JSON.parse(event.data);
      onRunEvent({ event: eventName, data });
    } catch (e) {
      console.error('Error parsing SSE event data in v2Client:', e);
    }
  };

  sse.onmessage = (e) => handleMsg(e, 'message');
  sse.addEventListener('connected', (e) => handleMsg(e as MessageEvent, 'connected'));
  sse.addEventListener('progress', (e) => handleMsg(e as MessageEvent, 'progress'));
  sse.addEventListener('completed', (e) => handleMsg(e as MessageEvent, 'completed'));
  sse.addEventListener('failed', (e) => handleMsg(e as MessageEvent, 'failed'));

  sse.onerror = (e) => {
    console.warn('v2 SSE connection encountered error or reloaded:', e);
  };

  return () => {
    sse.close();
  };
}
