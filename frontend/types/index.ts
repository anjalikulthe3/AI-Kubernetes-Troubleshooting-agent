export interface HealthResponse {
  status: string;
  service: string;
}

export interface Diagnosis {
  root_cause: string;
  explanation: string;
  fix: string;
  kubectl_command: string;
  prevention_recommendation?: string;
  confidence: number;
  confidence_reasoning?: string;
  analysis_source?: string;
  analysis_note?: string | null;
}

export interface ProgressEvent {
  step: string;
  status: "running" | "complete" | "error";
}

export interface InvestigateResponse {
  status: string;
  investigation: InvestigationPayload;
  diagnosis: Diagnosis | null;
  progress?: ProgressEvent[];
  message?: string | null;
}

export interface InvestigationPayload {
  pods: Record<string, unknown>;
  logs: Record<string, unknown>;
  events: Record<string, unknown>;
  deployments: Record<string, unknown>;
  network: Record<string, unknown>;
}

export interface InvestigationHistoryItem {
  id: string;
  user_id: string;
  created_at: string;
  root_cause: string;
  namespace: string;
  confidence: number;
  status: string;
}

export interface InvestigationStep {
  id: string;
  label: string;
}

export type StepStatus = "pending" | "running" | "complete" | "error";

export interface StepState {
  id: string;
  label: string;
  status: StepStatus;
}

export interface InsForgeUser {
  id: string;
  email?: string;
}

export interface ClusterInfo {
  context_name: string;
  cluster_name: string;
  server: string;
  is_current: boolean;
}

export interface ClustersResponse {
  clusters: ClusterInfo[];
  error?: string | null;
}
