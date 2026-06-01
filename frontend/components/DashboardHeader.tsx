"use client";

interface DashboardHeaderProps {
  email?: string;
  onSignOut: () => void;
}

export function DashboardHeader({ email, onSignOut }: DashboardHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-slate-800 pb-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">AI Kubernetes Agent</h1>
        <p className="mt-1 text-sm text-slate-400">
          Troubleshoot Kubernetes with AI
        </p>
      </div>

      <div className="flex items-center gap-4">
        {email ? <span className="text-sm text-slate-400">{email}</span> : null}
        <button
          type="button"
          onClick={onSignOut}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 transition hover:border-slate-500 hover:text-white"
        >
          Sign Out
        </button>
      </div>
    </header>
  );
}
