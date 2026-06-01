"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ClusterSelector } from "@/components/ClusterSelector";
import { DashboardHeader } from "@/components/DashboardHeader";
import { DiagnosisCard } from "@/components/DiagnosisCard";
import { HistoryTable } from "@/components/HistoryTable";
import { InvestigationProgress } from "@/components/InvestigationProgress";
import { useAuth } from "@/context/AuthContext";
import { useClusters } from "@/hooks/useClusters";
import { useInvestigation } from "@/hooks/useInvestigation";
import { useInvestigationHistory } from "@/hooks/useInvestigationHistory";
import { saveInvestigationHistory } from "@/services/history";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, signOut } = useAuth();
  const {
    steps,
    diagnosis,
    isInvestigating,
    error,
    runInvestigation,
    result,
  } = useInvestigation();
  const { history, loading: historyLoading, error: historyError, refresh } =
    useInvestigationHistory(user?.id);
  const { clusters, loading: clustersLoading, error: clustersError } = useClusters();

  const [selectedContext, setSelectedContext] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  // Auto-select the current context once clusters load
  useEffect(() => {
    if (clusters.length > 0 && selectedContext === null) {
      const current = clusters.find((c) => c.is_current);
      setSelectedContext((current ?? clusters[0]).context_name);
    }
  }, [clusters, selectedContext]);

  async function handleInvestigate() {
    if (!selectedContext) return;
    setActionError(null);
    const response = await runInvestigation(selectedContext);

    if (response && user) {
      try {
        await saveInvestigationHistory(user.id, response);
        await refresh();
      } catch {
        setActionError(
          "Investigation completed, but history could not be saved.",
        );
      }
    }
  }

  async function handleSignOut() {
    await signOut();
    router.replace("/login");
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
        <p className="text-sm text-slate-400">Loading dashboard…</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <DashboardHeader email={user.email} onSignOut={handleSignOut} />

        {/* Cluster picker */}
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <ClusterSelector
            clusters={clusters}
            loading={clustersLoading}
            error={clustersError}
            selectedContext={selectedContext}
            isInvestigating={isInvestigating}
            onSelect={setSelectedContext}
          />

          {clusters.length > 0 && (
            <div className="mt-6">
              <button
                type="button"
                onClick={handleInvestigate}
                disabled={isInvestigating || !selectedContext}
                className="w-full rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
              >
                {isInvestigating
                  ? `Investigating ${selectedContext}…`
                  : selectedContext
                    ? `Investigate ${selectedContext}`
                    : "Select a cluster"}
              </button>
            </div>
          )}

          {(error || actionError) && (
            <div className="mt-4 rounded-lg border border-red-800 bg-red-950/30 p-4">
              <p className="text-sm font-medium text-red-300">Investigation failed</p>
              <p className="mt-1 whitespace-pre-line text-sm text-red-400">
                {error || actionError}
              </p>
            </div>
          )}
        </section>

        {(isInvestigating || result) && <InvestigationProgress steps={steps} />}

        {diagnosis ? <DiagnosisCard diagnosis={diagnosis} /> : null}

        <HistoryTable
          history={history}
          loading={historyLoading}
          error={historyError}
        />
      </div>
    </main>
  );
}
