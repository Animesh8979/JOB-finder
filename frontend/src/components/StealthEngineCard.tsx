import React, { useState } from 'react';
import { ShieldCheck, RefreshCw, Terminal } from 'lucide-react';

interface StealthStatus {
  package_installed?: boolean;
  browser_fetched?: boolean;
  executable?: string;
  install_root?: string;
  engine_last_used?: string;
  package_version?: string | null;
  error?: string;
}

/**
 * Stealth Engine card — shows whether browser automation is running on
 * Camoufox (anti-detect Firefox) or the Chromium fallback, straight from
 * GET /api/v2/stealth-status. Read-only: fetching the binary is a terminal
 * job (setup.bat does it automatically).
 */
export default function StealthEngineCard() {
  const [status, setStatus] = useState<StealthStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/v2/stealth-status');
      setStatus(await r.json());
    } catch {
      setStatus({ error: 'Backend unreachable' });
    } finally {
      setLoading(false);
    }
  };

  // Lazy first load: only ask the backend when the settings page opens.
  if (!status && !loading) void load();

  const active = status?.browser_fetched && status?.package_installed;
  const headline = status?.error
    ? 'Unknown'
    : active
      ? 'Camoufox active'
      : status?.package_installed
        ? 'Installed — browser not fetched'
        : 'Chromium fallback';

  return (
    <div className="surface-panel p-6 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[#0df] flex items-center gap-2">
          <ShieldCheck size={20} />
          Stealth Engine
        </h2>
        <button
          onClick={load}
          title="Re-check engine status"
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-400 hover:text-white transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="flex items-center gap-3">
        <span
          className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
            active
              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
              : 'bg-zinc-500/10 text-zinc-300 border-zinc-500/25'
          }`}
        >
          {headline}
        </span>
        {status?.package_version && !status.error && (
          <span className="text-[11px] text-zinc-500 font-mono">v{status.package_version}</span>
        )}
      </div>

      <p className="text-sm text-gray-400 leading-relaxed">
        Browser automation uses <span className="text-gray-200 font-medium">Camoufox</span> — an open-source,
        anti-detect Firefox with C++-level fingerprint spoofing and humanized cursor movement.
        If it is not installed, automation transparently falls back to Playwright Chromium. Nothing is ever
        auto-submitted either way; you always review and click Submit.
      </p>

      {status && !status.error && (
        <div className="pt-2 border-t border-white/5 space-y-1 font-mono text-[11px] text-zinc-500 break-all">
          <div>engine_last_used: <span className="text-zinc-300">{status.engine_last_used || 'none yet'}</span></div>
          <div>install_root: <span className="text-zinc-300">{status.install_root}</span></div>
        </div>
      )}

      {!active && !status?.error && (
        <div className="flex items-start gap-2 pt-1 text-xs text-zinc-500">
          <Terminal size={13} className="mt-0.5 shrink-0" />
          <span>
            To enable: run <code className="text-indigo-300">setup.bat</code>, or manually{' '}
            <code className="text-indigo-300">pip install -U &quot;camoufox[geoip]&quot;</code> then{' '}
            <code className="text-indigo-300">python -m src.stealth_browser --fetch</code>.
          </span>
        </div>
      )}
    </div>
  );
}
