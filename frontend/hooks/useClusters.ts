"use client";

import { useEffect, useState } from "react";

import { getClusters } from "@/services/api";
import type { ClusterInfo } from "@/types";

export function useClusters() {
  const [clusters, setClusters] = useState<ClusterInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await getClusters();
        if (cancelled) return;
        if (response.error) {
          setError(response.error);
          setClusters([]);
        } else {
          setClusters(response.clusters);
          setError(null);
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load clusters.");
        setClusters([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { clusters, loading, error };
}
