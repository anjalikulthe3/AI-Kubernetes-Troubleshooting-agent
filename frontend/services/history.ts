"use client";

import { insforge, INVESTIGATIONS_TABLE } from "@/lib/insforge";
import { extractPrimaryNamespace } from "@/lib/investigation-steps";
import type { Diagnosis, InvestigateResponse } from "@/types";

export async function saveInvestigationHistory(
  userId: string,
  response: InvestigateResponse,
) {
  if (!insforge || !response.diagnosis) {
    return;
  }

  const diagnosis: Diagnosis = response.diagnosis;

  await insforge.database.from(INVESTIGATIONS_TABLE).insert({
    user_id: userId,
    root_cause: diagnosis.root_cause,
    namespace: extractPrimaryNamespace(response.investigation),
    confidence: diagnosis.confidence,
    status: response.status,
    created_at: new Date().toISOString(),
  });
}
