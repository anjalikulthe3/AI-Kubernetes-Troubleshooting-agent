import axios, { AxiosError } from "axios";

import type { ClustersResponse, HealthResponse, InvestigateResponse } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  timeout: 120_000,
});

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

export async function getClusters(): Promise<ClustersResponse> {
  try {
    const { data } = await api.get<ClustersResponse>("/clusters");
    return data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
          "Failed to load clusters. Is the backend running?",
      );
    }
    throw error;
  }
}

export async function investigateCluster(
  investigationId?: string,
  contextName?: string,
): Promise<InvestigateResponse> {
  try {
    const { data } = await api.post<InvestigateResponse>("/investigate", {
      investigation_id: investigationId ?? null,
      context_name: contextName ?? null,
    });
    return data;
  } catch (error) {
    if (error instanceof AxiosError) {
      if (error.code === "ECONNABORTED") {
        throw new Error("Investigation timed out. Please try again.");
      }
      const detail = error.response?.data?.detail;
      throw new Error(detail || "Investigation request failed.");
    }
    throw error;
  }
}

export function getApiErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong.";
}
