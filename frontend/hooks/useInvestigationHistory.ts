"use client";

import { useCallback, useEffect, useState } from "react";

import { insforge, INVESTIGATIONS_TABLE } from "@/lib/insforge";
import type { InvestigationHistoryItem } from "@/types";

export function useInvestigationHistory(userId: string | undefined) {
  const [history, setHistory] = useState<InvestigationHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    if (!userId || !insforge) {
      setHistory([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { data, error: queryError } = await insforge.database
        .from(INVESTIGATIONS_TABLE)
        .select("*")
        .eq("user_id", userId)
        .order("created_at", { ascending: false })
        .limit(10);

      if (queryError) {
        setError(queryError.message || "Unable to load investigation history.");
        setHistory([]);
        return;
      }

      setHistory((data as InvestigationHistoryItem[]) || []);
    } catch {
      setError("Unable to load investigation history.");
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return { history, loading, error, refresh: loadHistory };
}
