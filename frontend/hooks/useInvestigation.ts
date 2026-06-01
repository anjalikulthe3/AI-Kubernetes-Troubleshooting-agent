"use client";

import { useCallback, useState } from "react";

import { insforge } from "@/lib/insforge";
import {
  createInitialStepStates,
  INVESTIGATION_STEPS,
} from "@/lib/investigation-steps";
import { getApiErrorMessage, investigateCluster } from "@/services/api";
import type {
  Diagnosis,
  InvestigateResponse,
  StepState,
  StepStatus,
} from "@/types";

function applyProgressUpdate(
  steps: StepState[],
  stepId: string,
  status: StepStatus,
): StepState[] {
  return steps.map((step) => {
    if (step.id === stepId) {
      return { ...step, status };
    }

    if (status === "running") {
      const targetIndex = INVESTIGATION_STEPS.findIndex((item) => item.id === stepId);
      const currentIndex = INVESTIGATION_STEPS.findIndex((item) => item.id === step.id);
      if (currentIndex < targetIndex && step.status !== "complete") {
        return { ...step, status: "complete" };
      }
    }

    return step;
  });
}

function applyProgressEvents(
  steps: StepState[],
  events: Array<{ step: string; status: string }>,
): StepState[] {
  return events.reduce((current, event) => {
    return applyProgressUpdate(current, event.step, event.status as StepStatus);
  }, steps);
}

export function useInvestigation() {
  const [steps, setSteps] = useState<StepState[]>(createInitialStepStates);
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [result, setResult] = useState<InvestigateResponse | null>(null);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const publishProgress = useCallback(
    async (channel: string, stepId: string, status: StepStatus) => {
      setSteps((current) => applyProgressUpdate(current, stepId, status));

      if (!insforge) {
        return;
      }

      await insforge.realtime.publish(channel, "progress", {
        step: stepId,
        status,
      });
    },
    [],
  );

  const runInvestigation = useCallback(async (contextName?: string) => {
    setError(null);
    setDiagnosis(null);
    setResult(null);
    setSteps(createInitialStepStates());
    setIsInvestigating(true);

    const investigationId = crypto.randomUUID();
    const channel = `investigation:${investigationId}`;
    const progressHandler = (payload: { step?: string; status?: StepStatus }) => {
      if (payload.step && payload.status) {
        setSteps((current) =>
          applyProgressUpdate(current, payload.step!, payload.status!),
        );
      }
    };

    try {
      if (insforge) {
        await insforge.realtime.connect();
        insforge.realtime.on("progress", progressHandler);
        await insforge.realtime.subscribe(channel);
      }

      await publishProgress(channel, "pods", "running");

      const response = await investigateCluster(investigationId, contextName);

      if (response.progress?.length) {
        setSteps((current) => applyProgressEvents(current, response.progress!));

        if (insforge) {
          for (const event of response.progress) {
            await publishProgress(
              channel,
              event.step,
              event.status as StepStatus,
            );
          }
        }
      } else {
        for (const step of INVESTIGATION_STEPS) {
          await publishProgress(channel, step.id, "complete");
        }
      }

      setResult(response);
      setDiagnosis(response.diagnosis);
      return response;
    } catch (investigationError) {
      const message = getApiErrorMessage(investigationError);
      setError(message);
      setSteps((current) =>
        current.map((step) =>
          step.status === "running" ? { ...step, status: "error" } : step,
        ),
      );
      return null;
    } finally {
      if (insforge) {
        insforge.realtime.off("progress", progressHandler);
        insforge.realtime.unsubscribe(channel);
      }
      setIsInvestigating(false);
    }
  }, [publishProgress]);

  return {
    steps,
    diagnosis,
    result,
    isInvestigating,
    error,
    runInvestigation,
  };
}
