import type { Diagnosis } from "@/types";

interface DiagnosisCardProps {
  diagnosis: Diagnosis;
}

const HEALTHY_ROOT_CAUSE = "No active Kubernetes failure detected";

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const color =
    confidence >= 80
      ? "text-emerald-400"
      : confidence >= 60
        ? "text-amber-400"
        : "text-red-400";
  return <span className={`text-lg font-semibold ${color}`}>{confidence}%</span>;
}

function SourceBadge({ source }: { source?: string }) {
  if (!source) return null;
  const label =
    source === "llm" ? "AI" : source === "heuristic" ? "Heuristic" : "Rule-based";
  const color =
    source === "llm"
      ? "bg-blue-900/50 text-blue-300"
      : source === "heuristic"
        ? "bg-amber-900/50 text-amber-300"
        : "bg-slate-800 text-slate-300";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs ${color}`}>{label}</span>
  );
}

export function DiagnosisCard({ diagnosis }: DiagnosisCardProps) {
  const isHealthy = diagnosis.root_cause === HEALTHY_ROOT_CAUSE;

  if (isHealthy) {
    return (
      <section className="rounded-xl border border-emerald-800 bg-emerald-950/30 p-6">
        <div className="flex items-center gap-3">
          <span className="text-2xl text-emerald-400">✓</span>
          <div>
            <h2 className="text-lg font-medium text-emerald-300">
              No critical Kubernetes issues detected
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Cluster appears healthy. Re-run investigation if symptoms appear.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-medium text-white">Diagnosis</h2>
        <SourceBadge source={diagnosis.analysis_source} />
      </div>

      <div className="mt-5 space-y-4 text-sm">
        <div>
          <p className="text-slate-400">Root Cause</p>
          <p className="mt-1 font-medium text-white">{diagnosis.root_cause}</p>
        </div>

        <div>
          <p className="text-slate-400">Explanation</p>
          <p className="mt-1 text-slate-200">{diagnosis.explanation}</p>
        </div>

        <div>
          <p className="text-slate-400">Suggested Fix</p>
          <p className="mt-1 text-slate-200">{diagnosis.fix}</p>
        </div>

        <div>
          <p className="text-slate-400">kubectl Command</p>
          <code className="mt-1 block rounded-lg bg-slate-950 px-3 py-2 text-xs text-emerald-300">
            {diagnosis.kubectl_command}
          </code>
        </div>

        {diagnosis.prevention_recommendation && (
          <div>
            <p className="text-slate-400">Prevention</p>
            <p className="mt-1 text-slate-300 text-xs">{diagnosis.prevention_recommendation}</p>
          </div>
        )}

        <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-3">
          <div>
            <span className="text-slate-400">Confidence</span>
            {diagnosis.confidence_reasoning && (
              <p className="mt-0.5 text-xs text-slate-500">{diagnosis.confidence_reasoning}</p>
            )}
          </div>
          <ConfidenceBadge confidence={diagnosis.confidence} />
        </div>

        {diagnosis.analysis_note && (
          <p className="text-xs text-amber-400/80">
            Note: {diagnosis.analysis_note}
          </p>
        )}
      </div>
    </section>
  );
}
