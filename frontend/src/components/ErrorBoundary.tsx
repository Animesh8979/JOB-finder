import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface State {
  error: Error | null;
}

/**
 * App-level crash containment. A render error in any child previously
 * unmounted the whole React tree (white screen). This boundary catches it,
 * keeps the shell alive, and offers a soft reset of the failing subtree.
 */
export default class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  State
> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Local-first app: console is the right sink; no external reporting.
    console.error('UI crashed inside ErrorBoundary:', error, info.componentStack);
  }

  private reset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-[#08080a] text-slate-100">
        <div className="max-w-md w-full p-6 rounded-2xl bg-white/[0.02] border border-rose-500/25 space-y-4 text-center">
          <AlertTriangle size={32} className="mx-auto text-rose-400" />
          <h1 className="text-lg font-bold">Something broke in the interface</h1>
          <p className="text-xs text-zinc-400 font-mono break-all bg-black/40 rounded-lg p-3 text-left">
            {this.state.error.message}
          </p>
          <p className="text-sm text-zinc-400">
            Your data is safe — everything lives in <span className="font-mono">data/</span> on disk.
            Try reloading this panel.
          </p>
          <button
            onClick={this.reset}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-500/20 border border-indigo-500/40 text-indigo-200 hover:bg-indigo-500/30 transition-colors"
          >
            <RotateCcw size={14} />
            Reload panel
          </button>
        </div>
      </div>
    );
  }
}
