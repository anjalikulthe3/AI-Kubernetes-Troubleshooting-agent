import type { ClusterInfo } from "@/types";

interface ClusterSelectorProps {
  clusters: ClusterInfo[];
  loading: boolean;
  error: string | null;
  selectedContext: string | null;
  isInvestigating: boolean;
  onSelect: (contextName: string) => void;
}

export function ClusterSelector({
  clusters,
  loading,
  error,
  selectedContext,
  isInvestigating,
  onSelect,
}: ClusterSelectorProps) {
  if (loading) {
    return (
      <p className="text-sm text-slate-400">Loading clusters from kubeconfig…</p>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/40 p-4 text-sm text-red-300">
        <p className="font-medium">Could not load clusters</p>
        <p className="mt-1 whitespace-pre-line text-red-400">{error}</p>
      </div>
    );
  }

  if (clusters.length === 0) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 text-sm text-slate-400">
        No clusters found in kubeconfig.
        <br />
        Verify your <code className="text-slate-300">KUBECONFIG_PATH</code> or
        place a valid kubeconfig at <code className="text-slate-300">~/.kube/config</code>.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-slate-300">
        Select a cluster to investigate:
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {clusters.map((cluster) => {
          const isSelected = selectedContext === cluster.context_name;
          return (
            <button
              key={cluster.context_name}
              type="button"
              disabled={isInvestigating}
              onClick={() => onSelect(cluster.context_name)}
              className={[
                "flex flex-col gap-1 rounded-lg border p-4 text-left transition",
                "disabled:cursor-not-allowed disabled:opacity-50",
                isSelected
                  ? "border-blue-500 bg-blue-950/50 ring-1 ring-blue-500"
                  : "border-slate-700 bg-slate-900/50 hover:border-slate-500 hover:bg-slate-800/50",
              ].join(" ")}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm font-medium text-white">
                  {cluster.context_name}
                </span>
                {cluster.is_current && (
                  <span className="shrink-0 rounded-full bg-emerald-900/60 px-2 py-0.5 text-xs text-emerald-400">
                    current
                  </span>
                )}
              </div>
              {cluster.server && (
                <span className="truncate text-xs text-slate-400">
                  {cluster.server}
                </span>
              )}
              {cluster.cluster_name !== cluster.context_name && (
                <span className="truncate text-xs text-slate-500">
                  cluster: {cluster.cluster_name}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
