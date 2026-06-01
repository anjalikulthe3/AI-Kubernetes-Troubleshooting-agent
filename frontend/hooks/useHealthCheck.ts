"use client";

import { useQuery } from "@tanstack/react-query";

import { getHealth } from "@/services/api";

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });
}
