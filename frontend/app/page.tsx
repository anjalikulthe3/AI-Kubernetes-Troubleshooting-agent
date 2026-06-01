"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/context/AuthContext";
import { useHealthCheck } from "@/hooks/useHealthCheck";

export default function HomePage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const { data, isLoading, isError } = useHealthCheck();

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  const systemStatus = isLoading
    ? "Checking..."
    : isError
      ? "Unavailable"
      : data?.status === "healthy"
        ? "Ready"
        : "Degraded";

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900/60 p-10 text-center shadow-xl">
        <h1 className="text-3xl font-semibold tracking-tight text-white">
          AI Kubernetes Agent
        </h1>
        <p className="mt-3 text-base text-slate-400">
          Troubleshoot Kubernetes with AI
        </p>

        <Link
          href="/login"
          className="mt-8 inline-flex w-full items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition hover:bg-blue-500"
        >
          Open Dashboard
        </Link>

        <p className="mt-6 text-sm text-slate-400">
          System Status:{" "}
          <span
            className={
              systemStatus === "Ready"
                ? "font-medium text-emerald-400"
                : systemStatus === "Checking..."
                  ? "font-medium text-amber-400"
                  : "font-medium text-red-400"
            }
          >
            {systemStatus}
          </span>
        </p>
      </div>
    </main>
  );
}
