import type { StepState } from "@/types";

interface InvestigationProgressProps {
  steps: StepState[];
}

function statusIcon(status: StepState["status"]) {
  switch (status) {
    case "complete":
      return "✓";
    case "running":
      return "…";
    case "error":
      return "✕";
    default:
      return "○";
  }
}

export function InvestigationProgress({ steps }: InvestigationProgressProps) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-medium text-white">Investigation Status</h2>
      <ul className="mt-4 space-y-3">
        {steps.map((step) => (
          <li
            key={step.id}
            className="flex items-center gap-3 text-sm text-slate-300"
          >
            <span
              className={
                step.status === "complete"
                  ? "text-emerald-400"
                  : step.status === "running"
                    ? "text-amber-400"
                    : step.status === "error"
                      ? "text-red-400"
                      : "text-slate-500"
              }
            >
              {statusIcon(step.status)}
            </span>
            <span
              className={
                step.status === "running" ? "font-medium text-white" : undefined
              }
            >
              {step.label}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
