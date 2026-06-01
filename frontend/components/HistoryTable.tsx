import type { InvestigationHistoryItem } from "@/types";

interface HistoryTableProps {
  history: InvestigationHistoryItem[];
  loading: boolean;
  error: string | null;
}

export function HistoryTable({ history, loading, error }: HistoryTableProps) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-medium text-white">Recent Investigations</h2>

      {loading ? (
        <p className="mt-4 text-sm text-slate-400">Loading history...</p>
      ) : error ? (
        <p className="mt-4 text-sm text-amber-400">{error}</p>
      ) : history.length === 0 ? (
        <p className="mt-4 text-sm text-slate-400">
          No investigations yet. Run your first cluster investigation above.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="pb-3 pr-4 font-medium">Root Cause</th>
                <th className="pb-3 pr-4 font-medium">Namespace</th>
                <th className="pb-3 pr-4 font-medium">Confidence</th>
                <th className="pb-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.id} className="border-t border-slate-800 text-slate-200">
                  <td className="py-3 pr-4">{item.root_cause}</td>
                  <td className="py-3 pr-4">{item.namespace}</td>
                  <td className="py-3 pr-4">{item.confidence}%</td>
                  <td className="py-3 capitalize">{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
