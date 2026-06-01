import type { InvestigationPayload, InvestigationStep } from "@/types";

export const INVESTIGATION_STEPS: InvestigationStep[] = [
  { id: "pods", label: "Checking Pods" },
  { id: "logs", label: "Reading Logs" },
  { id: "events", label: "Analyzing Events" },
  { id: "deployments", label: "Inspecting Deployments" },
  { id: "network", label: "Checking Networking" },
  { id: "ai_reasoning", label: "AI Reasoning" },
  { id: "root_cause", label: "Root Cause Found" },
];

export function createInitialStepStates() {
  return INVESTIGATION_STEPS.map((step) => ({
    ...step,
    status: "pending" as const,
  }));
}

export function extractPrimaryNamespace(
  investigation: InvestigationPayload | Record<string, unknown> | undefined,
): string {
  if (!investigation) {
    return "default";
  }

  const pods = investigation.pods as
    | { problematic_pods?: Array<{ namespace?: string }> }
    | undefined;
  const firstPod = pods?.problematic_pods?.[0];
  if (firstPod?.namespace) {
    return firstPod.namespace;
  }

  const deployments = investigation.deployments as
    | { problematic_deployments?: Array<{ namespace?: string }> }
    | undefined;
  const firstDeployment = deployments?.problematic_deployments?.[0];
  if (firstDeployment?.namespace) {
    return firstDeployment.namespace;
  }

  return "default";
}
